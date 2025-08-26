<?php
// --- Configuration ---
// The root directory of the project, which is one level up from the GUI directory.
$project_root = realpath(__DIR__ . '/../WPCV1');

// --- Input ---
$current_dir_relative = $_GET['dir'] ?? '';

// --- Security Validation ---
// Sanitize the input to prevent directory traversal.
// Normalize the path to remove '..' and '.' segments.
$current_dir_relative = str_replace('..', '', $current_dir_relative);
$current_dir_relative = ltrim($current_dir_relative, '/');

$current_dir_absolute = realpath($project_root . '/' . $current_dir_relative);

// Check if the resolved path is within the project root.
if (!$current_dir_absolute || strpos($current_dir_absolute, $project_root) !== 0) {
    http_response_code(400);
    echo json_encode(['error' => 'Access denied: Invalid directory.']);
    exit;
}

// --- Directory Scanning ---
try {
    $items = scandir($current_dir_absolute);
    $files = [];
    $dirs = [];

    foreach ($items as $item) {
        if ($item === '.' || $item === '..') {
            continue;
        }

        $path = $current_dir_absolute . '/' . $item;
        $relative_path = ltrim($current_dir_relative . '/' . $item, '/');

        if (is_dir($path)) {
            $dirs[] = ['name' => $item, 'path' => $relative_path];
        } else {
            $files[] = ['name' => $item, 'path' => $relative_path];
        }
    }

    // --- Response ---
    header('Content-Type: application/json');
    echo json_encode([
        'current_dir' => $current_dir_relative,
        'dirs' => $dirs,
        'files' => $files
    ]);

} catch (Exception $e) {
    http_response_code(500);
    echo json_encode(['error' => 'Error reading directory.']);
}
?>
