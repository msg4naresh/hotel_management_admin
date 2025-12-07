from app.services.s3_service import S3Service


def get_s3_service() -> S3Service:
    """Dependency for S3Service - creates new instance per request"""
    return S3Service()
