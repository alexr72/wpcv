<?php
$allowed_dirs = ['docs', 'logs'];
$selected_file = $_GET['file'] ?? '';

foreach ($allowed_dirs as $dir) {
    $path = __DIR__ . "/$dir/$selected_file";
    if (file_exists($path)) {
        echo "<pre>" . htmlspecialchars(file_get_contents($path)) . "</pre>";
        exit;
    }
}
echo "File not found or access denied.";
$allowedDirs = ['logs', 'docs'];
$file = basename($_GET['file'] ?? '');
$path = '';

foreach ($allowedDirs as $dir) {
  if (file_exists("$dir/$file")) {
    $path = "$dir/$file";
    break;
  }
}

if ($path) {
  echo "<pre>" . htmlspecialchars(file_get_contents($path)) . "</pre>";
} else {
  echo "⚠️ File not found or access denied.";
}
?>
