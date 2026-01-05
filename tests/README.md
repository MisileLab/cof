테스트 안내서입니다.

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
pytest tests/<파일명>.py
```

특정 테스트 클래스만 실행:

```bash
pytest tests/<파일명>.py::TestClass
```

특정 테스트 함수만 실행:

```bash
pytest tests/<파일명>.py::TestClass::test_function
```

자세한 출력과 함께 실행:

```bash
pytest -v
```

실패한 테스트만 다시 실행:

```bash
pytest --lf
```

## 참고

- 현재 테스트는 최소이며 향후 확장될 수 있습니다.
- 새로운 테스트는 `tests/` 아래에 추가하세요.
