import pytest

if __name__ == "__main__":
    pytest.main(
        args=[
            "testing/ ",
            "-v",
            "--no-header",
            "--tb=long",
            "-W ignore",
        ]
    )