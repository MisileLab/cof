# Cof Network Tests

UDP 소켓 기능을 테스트하는 테스트 모음입니다.

## 설치

테스트를 실행하기 전에 개발 의존성을 설치해야 합니다:

```bash
uv sync --dev
```

또는 pip를 사용하는 경우:

```bash
pip install -e ".[dev]"
```

## 테스트 실행

전체 테스트 실행:

```bash
pytest
```

특정 테스트 파일만 실행:

```bash
pytest tests/test_network.py
```

특정 테스트 클래스만 실행:

```bash
pytest tests/test_network.py::TestNetworkPacket
```

특정 테스트 함수만 실행:

```bash
pytest tests/test_network.py::TestNetworkPacket::test_packet_creation
```

자세한 출력과 함께 실행:

```bash
pytest -v
```

실패한 테스트만 다시 실행:

```bash
pytest --lf
```

## 테스트 구조

### TestNetworkPacket
- `test_packet_creation`: 패킷 생성 테스트
- `test_packet_pack_unpack`: 패킷 직렬화/역직렬화 테스트
- `test_packet_checksum_validation`: 체크섬 검증 테스트
- `test_packet_minimum_size_validation`: 최소 크기 검증 테스트
- `test_packet_with_empty_payload`: 빈 페이로드 처리 테스트
- `test_packet_with_large_payload`: 큰 페이로드 처리 테스트

### TestUDPClientServer
- `test_socket_creation`: UDP 소켓 생성 테스트
- `test_handshake_success`: 클라이언트-서버 핸드셰이크 성공 테스트
- `test_handshake_timeout`: 핸드셰이크 타임아웃 테스트
- `test_session_id_generation`: 세션 ID 생성 테스트

### TestPacketFragmentation
- `test_large_packet_detection`: 큰 패킷 감지 테스트

### TestSocketOperations
- `test_udp_socket_send_receive`: 기본 UDP 송수신 테스트
- `test_udp_socket_timeout`: UDP 타임아웃 테스트
- `test_udp_socket_multiple_packets`: 다중 패킷 전송 테스트

### TestRetryLogic
- `test_receive_packet_retry_count`: 재시도 로직 테스트

### TestErrorHandling
- `test_socket_not_initialized_error`: 소켓 미초기화 에러 처리 테스트
- `test_invalid_packet_type`: 잘못된 패킷 타입 처리 테스트

## 주의사항

- 일부 테스트는 로컬 UDP 포트(7357, 9999 등)를 사용합니다
- 테스트 실행 중 방화벽 경고가 나타날 수 있습니다
- 일부 테스트는 타이밍에 민감하여 느린 시스템에서는 실패할 수 있습니다
