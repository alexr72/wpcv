<?php
// --- Configuration ---
// Define the directories that are safe to be previewed.
// Using realpath to get the canonicalized absolute pathname.
$allowed_dirs = [
    'docs' => realpath(__DIR__ . '/../WPCV1/docs'),
    'logs' => realpath(__DIR__ . '/../WPCV1/logs'),
];

// --- Input ---
$selected_file = $_GET['file'] ?? '';

// Basic security check: prevent directory traversal attacks.
if (strpos($selected_file, '..') !== false || strpos($selected_file, '/') !== false || strpos($selected_file, '\\') !== false) {
    http_response_code(400);
    echo "Access denied: Invalid file path.";
    exit;
}

// --- File Location and Preview ---
$file_found = false;
foreach ($allowed_dirs as $dir_path) {
    if (!$dir_path) continue; // Skip if realpath failed

    $full_path = $dir_path . '/' . $selected_file;

    if (file_exists($full_path) && is_readable($full_path)) {
        // Set content type to plain text for better rendering of logs and md files.
        header('Content-Type: text/plain; charset=utf-8');
        echo file_get_contents($full_path);
        $file_found = true;
        exit;
    }
}

// --- Error Handling ---
if (!$file_found) {
    http_response_code(404);
    echo "File not found or access denied.";
}

?>
