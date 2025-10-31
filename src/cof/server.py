"""
Cof server implementation.
"""

import asyncio
import json
import logging
import socket
from pathlib import Path
from typing import Dict, Any, Optional, Tuple

from cof.models import Commit, Tree, TreeEntry
from cof.main import CofRepository
from cof.network import NetworkPacket, PacketType, CofProtocolError, RemoteRepository

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class NetworkServer:
    """UDP network server for cof repository."""

    def __init__(self, root_dir: str, config: Dict[str, Any]):
        self.root_dir = Path(root_dir).resolve()
        self.config = config
        self.packet_size = config["network"]["packet_size"]
        self.host = "0.0.0.0"
        self.port = 7357
        self.socket = None
        self.running = False

    async def start(self) -> None:
        """Start the network server."""
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.socket.bind((self.host, self.port))
        self.running = True
        
        logger.info(f"Cof server started on {self.host}:{self.port}")
        
        try:
            while self.running:
                try:
                    if not self.socket:
                        raise CofProtocolError("Socket not initialized")
                    data, addr = self.socket.recvfrom(self.packet_size * 2)
                    asyncio.create_task(self._handle_packet(data, addr))
                except Exception as e:
                    logger.error(f"Server error: {e}")
        finally:
            if self.socket:
                self.socket.close()

    async def stop(self) -> None:
        """Stop the network server."""
        self.running = False
        if self.socket:
            self.socket.close()

    async def _handle_packet(self, data: bytes, addr: Tuple[str, int]) -> None:
        """Handle incoming packet."""
        try:
            packet = NetworkPacket.unpack(data)
            response = await self._process_packet(packet)
            
            if response and self.socket:
                response_data = response.pack()
                self.socket.sendto(response_data, addr)

        except Exception as e:
            logger.error(f"Packet handling error: {e}")
            # Send error response
            error_packet = NetworkPacket(
                packet_type=PacketType.ERROR,
                session_id="",
                repo_path="",
                sequence=0,
                total_packets=1,
                payload=str(e).encode()
            )
            if self.socket:
                self.socket.sendto(error_packet.pack(), addr)

    async def _process_packet(self, packet: NetworkPacket) -> Optional[NetworkPacket]:
        """Process packet and return response."""
        try:
            repo_path = self.root_dir / packet.repo_path
            repository = CofRepository(str(repo_path))

            if not repository._is_repo():
                return NetworkPacket(
                    packet_type=PacketType.ERROR,
                    session_id=packet.session_id,
                    repo_path=packet.repo_path,
                    sequence=0,
                    total_packets=1,
                    payload=f"Repository not found at {packet.repo_path}".encode()
                )

            if packet.packet_type == PacketType.HANDSHAKE:
                return NetworkPacket(
                    packet_type=PacketType.HANDSHAKE_ACK,
                    session_id=packet.session_id,
                    repo_path=packet.repo_path,
                    sequence=0,
                    total_packets=1,
                    payload=json.dumps({"status": "ok"}).encode()
                )

            elif packet.packet_type == PacketType.OBJECT_REQUEST:
                object_hash = packet.payload.decode()
                obj_data = repository._load_object(object_hash)
                
                if obj_data:
                    obj_bytes = json.dumps(obj_data).encode()
                    return NetworkPacket(
                        packet_type=PacketType.OBJECT_RESPONSE,
                        session_id=packet.session_id,
                        repo_path=packet.repo_path,
                        sequence=0,
                        total_packets=1,
                        payload=obj_bytes
                    )
                else:
                    return NetworkPacket(
                        packet_type=PacketType.ERROR,
                        session_id=packet.session_id,
                        repo_path=packet.repo_path,
                        sequence=0,
                        total_packets=1,
                        payload=f"Object {object_hash} not found".encode()
                    )

            elif packet.packet_type == PacketType.REF_REQUEST:
                refs = {}
                refs_dir = repository.cof_dir / "refs" / "heads"
                
                if refs_dir.exists():
                    for ref_file in refs_dir.iterdir():
                        with open(ref_file, "r") as f:
                            refs[ref_file.name] = f.read().strip()
                
                return NetworkPacket(
                    packet_type=PacketType.REF_RESPONSE,
                    session_id=packet.session_id,
                    repo_path=packet.repo_path,
                    sequence=0,
                    total_packets=1,
                    payload=json.dumps(refs).encode()
                )

            elif packet.packet_type == PacketType.PUSH_REQUEST:
                # Handle push request - would need more complex logic for real implementation
                return NetworkPacket(
                    packet_type=PacketType.PUSH_RESPONSE,
                    session_id=packet.session_id,
                    repo_path=packet.repo_path,
                    sequence=0,
                    total_packets=1,
                    payload=json.dumps({"status": "received"}).encode()
                )

            else:
                return NetworkPacket(
                    packet_type=PacketType.ERROR,
                    session_id=packet.session_id,
                    repo_path=packet.repo_path,
                    sequence=0,
                    total_packets=1,
                    payload=f"Unknown packet type: {packet.packet_type}".encode()
                )

        except Exception as e:
            logger.error(f"Packet processing error: {e}")
            return NetworkPacket(
                packet_type=PacketType.ERROR,
                session_id=packet.session_id,
                repo_path=packet.repo_path,
                sequence=0,
                total_packets=1,
                payload=str(e).encode()
            )