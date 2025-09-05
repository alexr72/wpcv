<?php
header('Content-Type: application/json');

$agents_file = __DIR__ . '/../WPCV1/config/agents.json';

if (!file_exists($agents_file)) {
    http_response_code(500);
    echo json_encode(['error' => 'Agents configuration file not found.']);
    exit;
}

$agents_config = json_decode(file_get_contents($agents_file), true);

if (json_last_error() !== JSON_ERROR_NONE) {
    http_response_code(500);
    echo json_encode(['error' => 'Error parsing agents configuration file.']);
    exit;
}

$agent_names = array_keys($agents_config);

echo json_encode($agent_names);
?>
