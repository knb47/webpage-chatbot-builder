from .models import UploadedFile, Deployment
import logging

logger = logging.getLogger(__name__)

def mock_deploy_chat_app(user_id, relative_file_path):
    """
    Mock function to simulate deploying a chat application.

    Args:
        user_id (int): The ID of the user who owns the uploaded file.
        relative_file_path (str): The path to the uploaded file relative to the media directory.

    Returns:
        dict: A dictionary containing the status of the mock deployment, endpoint, file path,
              file name, and a mock deployment ID.
    """
    try:
        logger.info(f"Mock: Searching for UploadedFile with path: {relative_file_path} for user: {user_id}")

        # Simulate fetching an UploadedFile instance
        uploaded_file = UploadedFile.objects.get(file=relative_file_path, user_id=user_id)

        # Simulate successful deployment
        bot_name = f'mock_bot_{user_id}'
        mock_endpoint = f"http://mock-endpoint.com/{bot_name}"

        # Create a mock Deployment object
        deployment = Deployment.objects.create(
            user_id=user_id,
            config_file_path=uploaded_file.file.name,  # Store the relative file path
            config_file_name=uploaded_file.file_name,
            chatbot_name=bot_name,
            endpoint=mock_endpoint,
            status='active'  # Assuming 'active' is the intended status
        )

        logger.info(f"Mock Deployment created with ID: {deployment.id}")
        logger.info(f"Mock Deployment created with endpoint: {deployment.endpoint}")
        logger.info(f"Mock Deployment created with file name: {uploaded_file.file_name}") 

        return {
            'status': 'completed',
            'endpoint': mock_endpoint,
            'file_path': uploaded_file.file.name,  # Include relative file path
            'file_name': uploaded_file.file_name,  # Include the actual file name
            'deployment_id': deployment.id  # Include the deployment ID
        }
    except UploadedFile.DoesNotExist:
        logger.error(f"Mock: UploadedFile with path {relative_file_path} and user {user_id} does not exist.")
        return {'status': 'failed', 'error': 'UploadedFile matching query does not exist.'}
    except Exception as e:
        logger.error(f"Mock: Error deploying chat app for user {user_id}: {e}")
        return {'status': 'failed', 'error': str(e)}
    

def mock_teardown_operation(user_id, endpoint):
    # Simulate a teardown operation with mock data
    print(f"Teardown initiated for user {user_id} on endpoint {endpoint}")
    return {
        'status': 'pending',  # Start with a 'pending' status
        'endpoint': endpoint,
        'message': 'Teardown is in progress...'
    }