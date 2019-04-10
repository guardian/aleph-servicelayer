from servicelayer import env

# Redis cache
REDIS_URL = env.get('REDIS_URL')
REDIS_EXPIRE = env.to_int('REDIS_EXPIRE', 84600 * 7)

# General gRPC settings
GRPC_LB_POLICY = env.get('GRPC_LB_POLICY', 'round_robin')
GRPC_CONN_AGE = env.to_int('GRPC_CONN_AGE', 500)

# Microservice for OCR
OCR_SERVICE = env.get('OCR_SERVICE')

# # Entity extraction service
# NER_SERVICE = env.get('NER_SERVICE')

# Amazon client credentials
AWS_KEY_ID = env.get('AWS_ACCESS_KEY_ID')
AWS_SECRET_KEY = env.get('AWS_SECRET_ACCESS_KEY')
AWS_REGION = env.get('AWS_REGION', 'eu-west-1')

# Storage type (either 's3', 'gs', or 'file', i.e. local file system):
ARCHIVE_TYPE = env.get('ARCHIVE_TYPE', 'file')
ARCHIVE_BUCKET = env.get('ARCHIVE_BUCKET')
ARCHIVE_PATH = env.get('ARCHIVE_PATH')

QUEUE_HIGH = 'QUEUE_HIGH'
QUEUE_MEDIUM = 'QUEUE_MEDIUM'
QUEUE_LOW = 'QUEUE_LOW'

QUEUE_PRIORITIES = [
    QUEUE_HIGH,
    QUEUE_MEDIUM,
    QUEUE_LOW,
]
