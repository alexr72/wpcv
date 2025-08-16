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
