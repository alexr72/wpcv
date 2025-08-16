document.getElementById('launchForm').addEventListener('submit', function(e) {
  e.preventDefault();

  const formData = new FormData(this);

  fetch('orchestrator.php', {
    method: 'POST',
    body: formData
  })
  .then(response => response.text())
  .then(data => {
    document.getElementById('output').innerHTML = `<pre>${data}</pre>`;
  })
  .catch(error => {
    document.getElementById('output').innerHTML = `<pre>Error: ${error}</pre>`;
  });
});
function previewFile() {
  const file = document.getElementById("fileSelect").value;
  const infoMap = {
    "expectations.md": "Validation rules for code structure, comments, security, etc.",
    "session.log": "Execution logs from orchestrator and validators.",
    "conversation.txt": "Full history of prompts and AI responses.",
    "context.json": "Last prompt, response, timestamp, and user metadata."
  };

  document.getElementById("fileInfo").innerText = infoMap[file] || "";

  fetch(`preview.php?file=${file}`)
    .then(response => response.text())
    .then(data => {
      document.getElementById("filePreview").innerText = data;
    })
    .catch(err => {
      document.getElementById("filePreview").innerText = "Error loading file.";
    });
}
