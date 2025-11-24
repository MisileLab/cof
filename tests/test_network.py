"""
Tests for UDP socket functionality in cof network module.
Tests packet creation, fragmentation, client-server communication, and reliability.
"""

import asyncio
import json
import pytest
import socket
import time
import uuid
from pathlib import Path
from typing import Dict, Any, Optional

from cof.network import (
    NetworkPacket,
    PacketType,
    NetworkClient,
    NetworkServer,
    CofProtocolError
)
from cof.models import RemoteRepository


@pytest.fixture
def test_config() -> Dict[str, Any]:
    """Create test configuration."""
    return {
        "network": {
            "packet_size": 1024,
            "timeout_ms": 1000,
            "max_retries": 3
        }
    }


@pytest.fixture
def test_remote() -> RemoteRepository:
    """Create test remote repository."""
    return RemoteRepository(
        name="test_remote",
        url="cof://127.0.0.1:7357/test_repo",
        host="127.0.0.1",
        port=7357,
        repo_path="test_repo"
    )


class TestNetworkPacket:
    """Test NetworkPacket pack/unpack and checksum validation."""

    def test_packet_creation(self):
        """Test basic packet creation."""
        packet = NetworkPacket(
            packet_type=PacketType.HANDSHAKE,
            session_id="test-session-id",
            repo_path="test/repo",
            sequence=0,
            total_packets=1,
            payload=b"test payload"
        )

        assert packet.packet_type == PacketType.HANDSHAKE
        assert packet.session_id == "test-session-id"
        assert packet.repo_path == "test/repo"
        assert packet.sequence == 0
        assert packet.total_packets == 1
        assert packet.payload == b"test payload"
        assert len(packet.checksum) == 16  # BLAKE3 checksum truncated to 16 chars

    def test_packet_pack_unpack(self):
        """Test packet serialization and deserialization."""
        original_packet = NetworkPacket(
            packet_type=PacketType.DATA,
            session_id="session123",
            repo_path="my/repo/path",
            sequence=5,
            total_packets=10,
            payload=b"some test data here"
        )

        # Pack the packet
        packed_data = original_packet.pack()

        # Unpack it back
        unpacked_packet = NetworkPacket.unpack(packed_data)

        # Verify all fields match
        assert unpacked_packet.packet_type == original_packet.packet_type
        assert unpacked_packet.session_id == original_packet.session_id
        assert unpacked_packet.repo_path == original_packet.repo_path
        assert unpacked_packet.sequence == original_packet.sequence
        assert unpacked_packet.total_packets == original_packet.total_packets
        assert unpacked_packet.payload == original_packet.payload
        assert unpacked_packet.checksum == original_packet.checksum

    def test_packet_checksum_validation(self):
        """Test that corrupted packets are rejected."""
        packet = NetworkPacket(
            packet_type=PacketType.HANDSHAKE,
            session_id="test-session",
            repo_path="repo",
            sequence=0,
            total_packets=1,
            payload=b"data"
        )

        packed_data = packet.pack()

        # Corrupt the checksum
        corrupted_data = b"0000000000000000" + packed_data[16:]

        # Should raise ValueError due to checksum mismatch
        with pytest.raises(ValueError, match="checksum mismatch"):
            NetworkPacket.unpack(corrupted_data)

    def test_packet_minimum_size_validation(self):
        """Test that packets below minimum size are rejected."""
        with pytest.raises(ValueError, match="Packet too small"):
            NetworkPacket.unpack(b"too short")

    def test_packet_with_empty_payload(self):
        """Test packet with empty payload."""
        packet = NetworkPacket(
            packet_type=PacketType.REF_REQUEST,
            session_id="session-id",
            repo_path="repo",
            sequence=0,
            total_packets=1,
            payload=b""
        )

        packed_data = packet.pack()
        unpacked_packet = NetworkPacket.unpack(packed_data)

        assert unpacked_packet.payload == b""

    def test_packet_with_large_payload(self):
        """Test packet with large payload."""
        large_payload = b"x" * 10000
        packet = NetworkPacket(
            packet_type=PacketType.DATA,
            session_id="large-test",
            repo_path="repo",
            sequence=0,
            total_packets=1,
            payload=large_payload
        )

        packed_data = packet.pack()
        unpacked_packet = NetworkPacket.unpack(packed_data)

        assert unpacked_packet.payload == large_payload


class TestUDPClientServer:
    """Test UDP client-server communication."""

    @pytest.mark.asyncio
    async def test_socket_creation(self, test_config):
        """Test that UDP sockets are created correctly."""
        async with NetworkClient(test_config) as client:
            assert client.socket is not None
            assert client.socket.type == socket.SOCK_DGRAM

    @pytest.mark.asyncio
    @pytest.mark.timeout(5)
    async def test_handshake_with_mock_server(self, test_config, test_remote):
        """Test handshake packet creation and structure (without real server)."""
        # This test validates the handshake packet format without requiring a server
        async with NetworkClient(test_config) as client:
            # Create handshake packet manually
            handshake_data = {"version": "1.0", "client": "cof"}
            handshake_packet = NetworkPacket(
                packet_type=PacketType.HANDSHAKE,
                session_id=client.session_id,
                repo_path=test_remote.repo_path,
                sequence=0,
                total_packets=1,
                payload=json.dumps(handshake_data).encode()
            )

            # Verify packet structure
            assert handshake_packet.packet_type == PacketType.HANDSHAKE
            assert len(handshake_packet.session_id) > 0
            assert handshake_packet.payload == json.dumps(handshake_data).encode()

            # Verify packet can be packed and unpacked
            packed = handshake_packet.pack()
            unpacked = NetworkPacket.unpack(packed)

            assert unpacked.packet_type == PacketType.HANDSHAKE
            # Full session ID should be preserved now
            assert unpacked.session_id == client.session_id

    @pytest.mark.asyncio
    @pytest.mark.timeout(10)
    async def test_handshake_timeout(self, test_config, test_remote):
        """Test handshake timeout when server is not available."""
        # Point to a port where no server is running
        test_remote.port = 9999

        # Reduce timeout for faster test
        test_config["network"]["timeout_ms"] = 500
        test_config["network"]["max_retries"] = 2

        async with NetworkClient(test_config) as client:
            result = await client.handshake(test_remote)
            # Should fail due to timeout
            assert result is False

    @pytest.mark.asyncio
    async def test_session_id_generation(self, test_config):
        """Test that each client gets a unique session ID."""
        async with NetworkClient(test_config) as client1:
            async with NetworkClient(test_config) as client2:
                assert client1.session_id != client2.session_id
                assert len(client1.session_id) > 0
                assert len(client2.session_id) > 0


class TestPacketFragmentation:
    """Test packet fragmentation and reassembly."""

    def test_large_packet_detection(self, test_config):
        """Test that large packets are detected for fragmentation."""
        large_payload = b"x" * 5000  # Larger than packet_size

        packet = NetworkPacket(
            packet_type=PacketType.DATA,
            session_id="test-session",
            repo_path="repo",
            sequence=0,
            total_packets=1,
            payload=large_payload
        )

        packed_data = packet.pack()

        # Packet data should be larger than configured packet size
        assert len(packed_data) > test_config["network"]["packet_size"]


class TestSocketOperations:
    """Test low-level socket operations."""

    def test_udp_socket_send_receive(self):
        """Test basic UDP socket send/receive functionality."""
        # Create two UDP sockets
        sender = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        receiver = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

        try:
            # Bind receiver to a specific port
            receiver.bind(("127.0.0.1", 0))  # Use any available port
            receiver_addr = receiver.getsockname()

            # Set timeout
            receiver.settimeout(1.0)

            # Send data
            test_data = b"Hello UDP!"
            sender.sendto(test_data, receiver_addr)

            # Receive data
            received_data, addr = receiver.recvfrom(1024)

            assert received_data == test_data

        finally:
            sender.close()
            receiver.close()

    def test_udp_socket_timeout(self):
        """Test UDP socket timeout behavior."""
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

        try:
            sock.bind(("127.0.0.1", 0))
            sock.settimeout(0.1)  # 100ms timeout

            # Try to receive when no data is sent
            with pytest.raises(socket.timeout):
                sock.recvfrom(1024)

        finally:
            sock.close()

    def test_udp_socket_multiple_packets(self):
        """Test sending multiple UDP packets."""
        sender = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        receiver = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

        try:
            receiver.bind(("127.0.0.1", 0))
            receiver_addr = receiver.getsockname()
            receiver.settimeout(1.0)

            # Send multiple packets
            packets = [b"packet1", b"packet2", b"packet3"]
            for packet in packets:
                sender.sendto(packet, receiver_addr)

            # Receive all packets
            received = []
            for _ in range(len(packets)):
                data, _ = receiver.recvfrom(1024)
                received.append(data)

            assert received == packets

        finally:
            sender.close()
            receiver.close()


class TestRetryLogic:
    """Test timeout and retry logic."""

    @pytest.mark.asyncio
    @pytest.mark.timeout(15)
    async def test_receive_packet_retry_count(self, test_config, test_remote):
        """Test that receive_packet respects max_retries configuration."""
        # Reduce timeout for faster test
        test_config["network"]["timeout_ms"] = 500
        test_config["network"]["max_retries"] = 2

        async with NetworkClient(test_config) as client:
            start_time = time.time()

            # Point to non-existent server to trigger retries
            test_remote.port = 9998

            try:
                # This should retry max_retries times
                await client.handshake(test_remote)
            except Exception:
                pass  # Expected to fail

            elapsed = time.time() - start_time

            # Should take at least (timeout_ms * max_retries) milliseconds
            min_expected_time = (test_config["network"]["timeout_ms"] / 1000.0) * test_config["network"]["max_retries"]

            # Allow some tolerance for timing
            assert elapsed >= min_expected_time * 0.5


class TestErrorHandling:
    """Test error handling in network operations."""

    @pytest.mark.asyncio
    @pytest.mark.timeout(5)
    async def test_socket_not_initialized_error(self, test_config, test_remote):
        """Test error when socket is not initialized."""
        client = NetworkClient(test_config)
        # Don't use async context manager, so socket is not initialized

        packet = NetworkPacket(
            packet_type=PacketType.HANDSHAKE,
            session_id="test",
            repo_path="repo",
            sequence=0,
            total_packets=1,
            payload=b""
        )

        with pytest.raises(CofProtocolError, match="Socket not initialized"):
            await client._send_packet(test_remote, packet)

    def test_invalid_packet_type(self):
        """Test handling of invalid packet type."""
        # Create packet data with invalid type
        invalid_packet_data = NetworkPacket(
            packet_type=PacketType.HANDSHAKE,
            session_id="test",
            repo_path="repo",
            sequence=0,
            total_packets=1,
            payload=b""
        ).pack()

        # Corrupt the packet type byte
        corrupted = bytearray(invalid_packet_data)
        corrupted[16] = 0xFF  # Invalid packet type

        # Recalculate checksum for the corrupted data
        import blake3
        checksum = blake3.blake3(bytes(corrupted[16:])).hexdigest()[:16]
        corrupted[:16] = checksum.encode('utf-8')

        # Should be able to unpack but with ERROR packet type
        packet = NetworkPacket.unpack(bytes(corrupted))
        assert packet.packet_type == PacketType.ERROR


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
