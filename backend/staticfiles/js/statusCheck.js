/**
 * statusCheck.js
 * 
 * This JavaScript module is responsible for handling asynchronous status checks for deployment and teardown tasks.
 * It communicates with the server to check the current status of these tasks and updates the UI accordingly.
 * 
 * Functions:
 * - checkStatus(taskId, itemId, type): Repeatedly checks the status of a task by polling the server until completion or failure.
 * - handleCompletion(data, itemId, type): Handles the UI updates when a task is successfully completed.
 * - handleError(error, itemId, type): Handles errors that occur during status checks and updates the UI accordingly.
 * 
 * Usage:
 * - This module is typically used in conjunction with an HTML page that lists deployment tasks.
 * - Each task should have an associated <li> element with a specific ID pattern and buttons with specific data attributes.
 * 
 * Reconciliation with HTML (e.g., library.html):
 * - Ensure that each task <li> has an ID formatted as `${type}-${itemId}` (e.g., `deployment-14`).
 * - Ensure that the buttons inside the <li> have the following classes and data attributes:
 *   - Deploy Button: `btn btn-primary btn-sm deploy-button` with `data-file-id` matching the task ID.
 *   - Loading Button: `btn btn-secondary btn-sm deployment-loading-button` with `data-file-id` matching the task ID.
 * - Make sure that any changes to the HTML structure maintain these ID and class name conventions.
 * 
 * Extending the Module:
 * - To add new types of tasks, update the `checkStatus`, `handleCompletion`, and `handleError` functions to handle the new type.
 * - Ensure that any new task types are supported by the server-side endpoints and return appropriate status data.
 * - Update the HTML templates to include necessary IDs and classes for any new task types.
 * 
 * Notes:
 * - This script relies on the server to provide accurate status updates. Ensure that the server endpoints are robust and handle errors gracefully.
 * - Use `console.log` and `showNotification` to help debug and notify users of errors and completions.
 */

function checkStatus(taskId, itemId, type) {
  return new Promise((resolve, reject) => {
    const check = async () => {
      try {
        let url = '';
        if (type === 'deployment') {
          url = `/account/deployment_status/${taskId}/`;
        } else if (type === 'teardown') {
          url = `/account/teardown_status/${taskId}/`;
        } else {
          throw new Error('Unknown status type');
        }

        const response = await fetch(url);
        const data = await response.json();
        console.log('Response data:', data);

        if (data.status === 'pending') {
          setTimeout(check, 5000);
        } else if (data.status === 'completed') {
          console.log('Task completed:', data);
          handleCompletion(data, itemId, type);
          resolve(data);
        } else {
          console.log('Task error:', data.error);
          handleError(data.error, itemId, type);
          reject(new Error(data.error));
        }
      } catch (error) {
        console.error('Error:', error);
        showNotification('An error occurred while checking status', 'error');
        reject(error);
      }
    };

    check();
  });
}

function handleCompletion(data, itemId, type) {
  const itemIdSelector = `${type}-${itemId}`;
  console.log(`Looking for element with ID: ${itemIdSelector}`);

  const item = document.getElementById(itemIdSelector);

  if (!item) {
    console.error(`Element with ID ${itemIdSelector} not found`);
    showNotification('Error: Item not found in DOM', 'error');
    return;
  }

  const button = item.querySelector(`.deploy-button[data-file-id="${itemId}"]`);
  const loadingButton = item.querySelector(`.deployment-loading-button[data-file-id="${itemId}"]`);

  if (!button) {
    console.error(`Deploy button not found in element with ID ${itemIdSelector}`);
    showNotification('Error: Deploy button not found in DOM', 'error');
    return;
  }

  if (!loadingButton) {
    console.error(`Loading button not found in element with ID ${itemIdSelector}`);
    showNotification('Error: Loading button not found in DOM', 'error');
    return;
  }

  if (type === 'deployment') {
    button.style.display = 'inline-block';
    loadingButton.style.display = 'none';
    
    // Disable the deploy button after successful deployment
    button.disabled = true;
    button.classList.add('opacity-50', 'cursor-not-allowed');

    const deployedText = item.querySelector('.deployed-text');
    if (deployedText) {
      deployedText.style.display = 'block';
    } else {
      console.warn(`.deployed-text not found in element with ID ${itemIdSelector}`);
    }

    showNotification(`Deployment for '${data.file_name}' completed! <a href="/account/deployments/">Click here</a> to see your deployment.`, 'success');
    button.setAttribute('data-deployed', 'true');
  } else if (type === 'teardown') {
    item.remove();
    showNotification(`Teardown for '${data.endpoint}' completed!`, 'success');
    if (document.getElementById('deployment-list').children.length === 0) {
      document.getElementById('deployment-list').innerHTML = '<li>No deployments found.</li>';
    }
  }
}

function handleError(error, itemId, type) {
  const itemIdSelector = `${type}-${itemId}`;
  const item = document.getElementById(itemIdSelector);

  if (!item) {
    console.error(`Element with ID ${itemIdSelector} not found during error handling`);
    showNotification('Error: Item not found in DOM during error handling', 'error');
    return;
  }

  const button = item.querySelector(`.deploy-button[data-file-id="${itemId}"]`);
  const loadingButton = item.querySelector(`.deployment-loading-button[data-file-id="${itemId}"]`);

  if (!button) {
    console.error(`Deploy button not found in element with ID ${itemIdSelector}`);
    showNotification('Error: Deploy button not found in DOM during error handling', 'error');
    return;
  }

  if (!loadingButton) {
    console.error(`Loading button not found in element with ID ${itemIdSelector}`);
    showNotification('Error: Loading button not found in DOM during error handling', 'error');
    return;
  }

  button.style.display = 'inline-block';
  loadingButton.style.display = 'none';

  showNotification(`An error occurred while during the deployment process: ${error}`, 'error');
}