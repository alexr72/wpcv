<?php
if ($_SERVER['REQUEST_METHOD'] === 'POST') {
  $mode = escapeshellarg($_POST['mode']);
  $agent = escapeshellarg($_POST['agent']);
  $folder = escapeshellarg($_POST['folder']);
  $expectation = escapeshellarg($_POST['expectation']);

  $cmd = "python3 $folder/WPCV1.py --mode $mode --agent $agent --folder $folder --expectation $expectation";
  $output = shell_exec($cmd);
  echo nl2br($output);
}
?>
