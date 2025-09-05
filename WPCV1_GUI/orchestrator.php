<?php
// WPCV1 Orchestrator Backend

if ($_SERVER['REQUEST_METHOD'] !== 'POST') {
    http_response_code(405);
    echo 'Method Not Allowed';
    exit;
}

// --- Configuration ---
$python_executable = 'python3';
// The Python script is located one directory up from the current script's location.
$python_script_path = realpath(__DIR__ . '/../WPCV1/WPCV1.py');

if (!$python_script_path || !is_executable($python_script_path)) {
    http_response_code(500);
    echo "Error: Python script not found or not executable at $python_script_path";
    exit;
}

// --- Input Sanitization ---
$mode = isset($_POST['mode']) ? escapeshellarg($_POST['mode']) : '';
$agent = isset($_POST['agent']) ? escapeshellarg($_POST['agent']) : '';
$file = isset($_POST['file']) ? escapeshellarg($_POST['file']) : '';
$expectation = isset($_POST['expectation']) ? escapeshellarg($_POST['expectation']) : '';
$directory = isset($_POST['directory']) ? escapeshellarg($_POST['directory']) : '';
$prompt = isset($_POST['prompt']) ? escapeshellarg($_POST['prompt']) : '';

if (empty($mode)) {
    http_response_code(400);
    echo 'Error: Mode is a required parameter.';
    exit;
}

// --- Command Building ---
$cmd = "$python_executable $python_script_path --mode $mode";

// Add arguments based on the mode
$mode_unquoted = trim($mode, "'");
if ($mode_unquoted === 'prompt' && !empty($agent)) {
    $cmd .= " --agent $agent";
    if (!empty($directory)) {
        $cmd .= " --directory $directory";
    }
    if (!empty($prompt)) {
        $cmd .= " --prompt $prompt";
    }
} elseif ($mode_unquoted === 'validate' && !empty($file)) {
    $cmd .= " --file $file";
    if (!empty($expectation)) {
        $cmd .= " --expect $expectation";
    }
} elseif ($mode_unquoted === 'scaffold') {
    // No additional arguments needed for scaffold mode
}

// Redirect stderr to stdout to capture errors from the script
$cmd .= " 2>&1";

// --- Execution ---
$output = [];
$return_var = -1;

exec($cmd, $output, $return_var);

// --- Response ---
if ($return_var !== 0) {
    http_response_code(500);
    echo "Error executing Python script (exit code: $return_var):\n";
}

echo implode("\n", $output);

?>
