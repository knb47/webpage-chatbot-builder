function checkStatus(taskId, deploymentId, type) {
  const check = async () => {
      try {
          const url = `/account/teardown_status/${taskId}/`;
          const response = await fetch(url);
          const data = await response.json();

          if (data.status === 'pending') {
              setTimeout(() => check(taskId, deploymentId, type), 5000);
          } else if (data.status === 'completed') {
              handleCompletion(data, deploymentId, type);
          } else {
              handleError(data.message, deploymentId, type);
          }
      } catch (error) {
          handleError(error.message, deploymentId, type);
      }
  };

  check();
}

function handleCompletion(data, deploymentId, type) {
  const deploymentSelector = `deployment-${deploymentId}`;
  const item = document.getElementById(deploymentSelector);
  const statusText = item.querySelector('p[role="status-text"]');
  const endButton = item.querySelector('.teardown-button');
  const loadingButton = item.querySelector('.teardown-loading-button');

  loadingButton.style.display = 'none';
  
  // Update status text and show delete button only
  statusText.textContent = `Status: ${data.deployment_status}`;
  endButton.style.display = 'none'; // Hide end button if still visible

  const deleteButton = document.createElement('button');
  deleteButton.className = 'btn btn-danger btn-sm delete-deployment';
  deleteButton.textContent = 'Delete';
  deleteButton.onclick = function() {
      handleDelete(deploymentId);
  };

  // Append only if a delete button does not already exist
  if (!item.querySelector('.delete-deployment')) {
      item.querySelector('.flex.space-x-2').appendChild(deleteButton);
  }

  showNotification(`Teardown for '${data.endpoint}' completed successfully!`, 'success');
}

function handleError(message, deploymentId, type) {
  const deploymentSelector = `deployment-${deploymentId}`;
  const item = document.getElementById(deploymentSelector);
  const endButton = item.querySelector('.teardown-button');
  const loadingButton = item.querySelector('.teardown-loading-button');

  showNotification(`An error occurred while ending the deployment: ${message}`, 'error');
  endButton.style.display = 'inline-block';
  loadingButton.style.display = 'none';
}
