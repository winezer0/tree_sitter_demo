<?php
spl_autoload_register(function ($class) {
    // 替换命名空间前缀为目录
    $prefix = 'DemoProject\\';
    $baseDir = __DIR__ . '/src/';

    // 检查类是否使用指定前缀
    $len = strlen($prefix);
    if (strncmp($prefix, $class, $len) !== 0) {
        return;
    }

    // 获取相对类名并转换为文件路径
    $relativeClass = substr($class, $len);
    $file = $baseDir . str_replace('\\', '/', $relativeClass) . '.php';

    // 如果文件存在则引入
    if (file_exists($file)) {
        require $file;
    }
});
?>