function getFilename(filePath) {
    // Split by forward or backward slashes and return the last part
    const parts = filePath.split(/[/\\]/);
    return parts[parts.length - 1];
}

document.getElementById('uploadButton').addEventListener('click', () => {
  const primaryFiles = document.getElementById('video1').files;
  const secondaryFile = document.getElementById('video2').files[0];
  const progressContainer = document.getElementById('progressContainer');
  progressContainer.innerHTML = ""; // Clear previous progress bars

  // Ensure each field has a selected file
  if (!secondaryFile) {
    alert("Please select a file to upload in the second field.");
    return;
  }
  if (primaryFiles.length === 0) {
    alert("Please select at least one file to process in the first field.");
    return;
  }

  fetch(`/get-job-code`)
  .then(response => response.json())
  .then(data => {
    jobCode = data.job_code;

    // Upload the secondary file first and get its path
    const secondaryIndex = 0;
    createProgressBars(secondaryFile, secondaryIndex, false);
    uploadSecondaryFile(secondaryFile, secondaryIndex, jobCode).then(response => {
      secondaryFilePath = response.file_path;

      // After the secondary file is uploaded, upload the primary files with the secondary file path
      for (let i = 0; i < primaryFiles.length; i++) {
        const file = primaryFiles[i];
        const primaryIndex = i + 1; // Ensure unique index for primary files
        createProgressBars(file, primaryIndex, true);
        uploadPrimaryFile(file, primaryIndex, secondaryFilePath, jobCode); // Pass secondary file path
      }
    });
  });
});

// Function to upload the secondary file and return its stored path
function uploadSecondaryFile(file, index, jobCode) {
  return new Promise((resolve, reject) => {
    const formData = new FormData();
    formData.append('file', file);
    formData.append('job_code', jobCode);

    const xhr = new XMLHttpRequest();
    xhr.open('POST', '/upload-secondary', true);

    xhr.upload.onprogress = (event) => {
      if (event.lengthComputable) {
        const percentComplete = (event.loaded / event.total) * 100;
        document.getElementById(`uploadProgress${index}`).style.width = percentComplete + '%';
        document.getElementById(`statusText${index}`).innerText = `Uploading ${file.name}: ${Math.round(percentComplete)}%`;
      }
    };

    xhr.onload = () => {
      if (xhr.status === 200) {
        const response = JSON.parse(xhr.responseText);
        document.getElementById(`statusText${index}`).innerText = `Upload complete for ${file.name}.`;

        // Remove the box after 1.5 seconds
        setTimeout(() => {
          const wrapper = document.getElementById(`statusText${index}`).parentNode;
          wrapper.remove();
        }, 1500);

        resolve(response); // Resolve with the file path & job code returned by the server
      } else {
        document.getElementById(`statusText${index}`).innerText = `Upload failed for ${file.name}.`;
        reject(new Error("Secondary file upload failed"));
      }
    };

    xhr.send(formData);
  });
}

// Function to upload primary files, with the secondary file path
function uploadPrimaryFile(file, index, secondaryFilePath, jobCode) {
  const formData = new FormData();
  formData.append('file', file);
  formData.append('secondary_file_path', secondaryFilePath); // Pass the path instead of the file
  formData.append('job_code', jobCode);

  const xhr = new XMLHttpRequest();
  xhr.open('POST', '/upload', true);

  xhr.upload.onprogress = (event) => {
    if (event.lengthComputable) {
      const percentComplete = (event.loaded / event.total) * 100;
      document.getElementById(`uploadProgress${index}`).style.width = percentComplete + '%';
      document.getElementById(`statusText${index}`).innerText = `Uploading ${file.name}: ${Math.round(percentComplete)}%`;
    }
  };

  xhr.onload = () => {
    if (xhr.status === 200) {
      document.getElementById(`filenameText${index}`).innerText = `Processing ${file.name}`;

      const response = JSON.parse(xhr.responseText);
      secondaryFilename = getFilename(secondaryFilePath);
      document.getElementById(`statusText${index}`).innerText = `with ${secondaryFilename}...`;
      checkProcessingProgress(response.file, index, jobCode, response);
    } else {
      document.getElementById(`statusText${index}`).innerText = `Upload failed for ${file.name}.`;
    }
  };

  xhr.send(formData);
}

function createProgressBars(file, index, requiresProcessing) {
  const wrapper = document.createElement('div');
  wrapper.className = 'progress-wrapper';

  const fileName = document.createElement('p');
  fileName.id = `filenameText${index}`;
  fileName.innerText = `Uploading ${file.name}`;
  wrapper.appendChild(fileName);

  const uploadProgress = document.createElement('div');
  uploadProgress.className = 'progress-bar';
  uploadProgress.id = `uploadProgress${index}`;
  wrapper.appendChild(uploadProgress);

  if (requiresProcessing) {
    const processingProgress = document.createElement('div');
    processingProgress.className = 'progress-bar processing';
    processingProgress.id = `processingProgress${index}`;
    wrapper.appendChild(processingProgress);
  }

  const statusText = document.createElement('p');
  statusText.id = `statusText${index}`;
  wrapper.appendChild(statusText);

  document.getElementById('progressContainer').appendChild(wrapper);
}

function checkProcessingProgress(filename, index, jobCode, response) {
  const intervalId = setInterval(() => {
    fetch(`/progress/${jobCode}/${filename}`)
      .then(response => response.json())
      .then(data => {
        const progress = data.processing_progress;
        document.getElementById(`processingProgress${index}`).style.width = progress + '%';

        if (progress === "100") {
          clearInterval(intervalId);
          document.getElementById(`filenameText${index}`).innerText = `${filename} processing complete!`;

          fetch(`/details/${jobCode}/${filename}`)
            .then(response2 => response2.json())
            .then(data2 => {

              // Display a summary box with file details and link after processing
              displayProcessedFileSummary(data2.video1, data2.video2, data2.out_video);
          });

          // Remove the progress bars and status after 3 seconds
          setTimeout(() => {
            const wrapper = document.getElementById(`statusText${index}`).parentNode;
            wrapper.remove();
          }, 3000); // 3 seconds delay
        }
      });
  }, 500); // Check every 500 ms
}

// Function to display the processed file summary box
function displayProcessedFileSummary(primaryFileName, secondaryFileName, downloadLink) {
    const summaryContainer = document.getElementById('processedFilesContainer');

    const summaryBox = document.createElement('div');
    summaryBox.className = 'summary-box';

    const closeButton = document.createElement('span');
    closeButton.className = 'close-btn';
    closeButton.innerHTML = '&times;';
    closeButton.onclick = () => {
        summaryBox.remove();
        updateActionButtons(); // Check if the action buttons need to be updated
    };
    summaryBox.appendChild(closeButton);

    const title = document.createElement('p');
    title.innerHTML = `<strong>Download the split video:</strong>`;
    summaryBox.appendChild(title);

    const downloadLinkElement = document.createElement('a');
    downloadLinkElement.href = downloadLink;
    downloadLinkElement.innerText = `${primaryFileName} + ${secondaryFileName}`;
    downloadLinkElement.target = "_blank";
    summaryBox.appendChild(downloadLinkElement);

    summaryContainer.appendChild(summaryBox);

    // Add animation
    setTimeout(() => summaryBox.classList.add('show'), 10);

    // Update action buttons
    updateActionButtons();
}

function updateActionButtons() {
    const summaryContainer = document.getElementById('processedFilesContainer');
    const boxes = summaryContainer.getElementsByClassName('summary-box');
    const closeAllButton = document.getElementById('closeAllButton');
    const downloadAllButton = document.getElementById('downloadAllButton');
    const buttonsContainer = document.getElementById('dynamicButtonsContainer');

    if (boxes.length >= 2) {
        if (!closeAllButton) {
            // Create "Close All" button
            const button = document.createElement('button');
            button.id = 'closeAllButton';
            button.innerText = 'Close All';
            button.onclick = () => {
                // Remove all summary boxes
                while (boxes.length > 0) {
                    boxes[0].remove();
                }
                updateActionButtons(); // Update the buttons' visibility
            };
            buttonsContainer.appendChild(button);
        }

        // Create "Download All" button if not present
        if (!downloadAllButton) {
            const downloadAll = document.createElement('button');
            downloadAll.id = 'downloadAllButton';
            downloadAll.innerText = 'Download All';
            downloadAll.onclick = () => downloadAllFiles();
            buttonsContainer.appendChild(downloadAll);
        }
    } else {
        // Remove the buttons if fewer than 2 boxes
        if (closeAllButton) closeAllButton.remove();
        if (downloadAllButton) downloadAllButton.remove();
    }
}

function downloadAllFiles() {
    const summaryContainer = document.getElementById('processedFilesContainer');
    const links = summaryContainer.getElementsByTagName('a'); // Get all links

    Array.from(links).forEach(link => {
        const anchor = document.createElement('a');
        anchor.href = link.href;
        anchor.download = ""; // Suggest downloading the file
        anchor.click();
    });
}
