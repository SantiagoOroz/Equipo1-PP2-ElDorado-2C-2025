<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Wiki API Wrapper - El Dorado</title>
    <style>
        body { font-family: Arial, sans-serif; max-width: 1200px; margin: 0 auto; padding: 20px; }
        .container { background: #f5f5f5; padding: 20px; border-radius: 8px; margin: 20px 0; }
        .form-group { margin: 15px 0; }
        label { display: block; margin-bottom: 5px; font-weight: bold; }
        input, select, textarea { width: 100%; padding: 8px; border: 1px solid #ddd; border-radius: 4px; }
        button { background: #007cba; color: white; padding: 10px 20px; border: none; border-radius: 4px; cursor: pointer; }
        button:hover { background: #005a87; }
        .result { background: white; padding: 20px; border-radius: 8px; margin-top: 20px; border-left: 4px solid #007cba; }
        .error { border-left-color: #dc3545; background: #f8d7da; }
        .success { border-left-color: #28a745; background: #d4edda; }
        pre { background: #f8f9fa; padding: 15px; border-radius: 4px; overflow-x: auto; }
        .tabs { display: flex; background: #e9ecef; border-radius: 4px 4px 0 0; }
        .tab { padding: 10px 20px; cursor: pointer; border: none; background: transparent; }
        .tab.active { background: white; border-bottom: 2px solid #007cba; }
        .tab-content { background: white; padding: 20px; border-radius: 0 0 4px 4px; }
    </style>
</head>
<body>
    <h1>🔧 Wiki API Wrapper - El Dorado</h1>
    
    <div class="container">
        <form method="post">
            <div class="form-group">
                <label for="action">Tipo de consulta:</label>
                <select name="action" id="action" required>
                    <option value="">Selecciona una acción</option>
                    <option value="search">Buscar páginas</option>
                    <option value="allpages">Listar todas las páginas</option>
                    <option value="content">Obtener contenido de página</option>
                    <option value="summary">Obtener resumen de página</option>
                </select>
            </div>
            
            <div class="form-group">
                <label for="query">Consulta/Título de página:</label>
                <input type="text" name="query" id="query" placeholder="Ej: hormigón, ACH 01, etc.">
            </div>
            
            <div class="form-group">
                <label for="limit">Límite de resultados:</label>
                <input type="number" name="limit" id="limit" value="10" min="1" max="100">
            </div>
            
            <div class="form-group">
                <label for="format">Formato de salida:</label>
                <select name="format" id="format">
                    <option value="json">JSON</option>
                    <option value="html">HTML</option>
                    <option value="text">Texto</option>
                    <option value="markdown">Markdown</option>
                </select>
            </div>
            
            <button type="submit">🚀 Ejecutar consulta</button>
        </form>
    </div>

    <?php
    if ($_POST) {
        require_once 'WikiApiWrapper.php';
        
        try {
            $wikiUrl = 'https://objetivos.eldoradosrl.ar/wiki';
            $username = 'Userapi';
            $password = 'pr0y3ct0llm';
            
            $wiki = new WikiApiWrapper($wikiUrl, $username, $password);
            $wiki->login();
            
            $action = $_POST['action'] ?? '';
            $query = $_POST['query'] ?? '';
            $limit = (int)($_POST['limit'] ?? 10);
            $format = $_POST['format'] ?? 'json';
            
            $result = null;
            $title = '';
            
            switch ($action) {
                case 'search':
                    $result = $wiki->searchPages($query, $limit);
                    $title = "Búsqueda: '$query'";
                    break;
                    
                case 'allpages':
                    $result = $wiki->getAllPages($limit);
                    $title = "Todas las páginas (límite: $limit)";
                    break;
                    
                case 'content':
                    $result = $wiki->getPageContent($query);
                    $title = "Contenido: '$query'";
                    break;
                    
                case 'summary':
                    $result = $wiki->getPageSummary($query);
                    $title = "Resumen: '$query'";
                    break;
                    
                default:
                    throw new Exception('Acción no válida');
            }
            
            if ($result) {
                $formattedResult = $wiki->formatOutput($result, $format);
                
                echo '<div class="result success">';
                echo '<h3>✅ ' . htmlspecialchars($title) . '</h3>';
                
                // Pestañas para mostrar diferentes formatos
                echo '<div class="tabs">';
                $formats = ['json', 'html', 'text', 'markdown'];
                foreach ($formats as $f) {
                    $active = $f === $format ? 'active' : '';
                    echo "<button class='tab $active' onclick='showFormat(\"$f\")'>" . strtoupper($f) . "</button>";
                }
                echo '</div>';
                
                // Contenido de las pestañas
                foreach ($formats as $f) {
                    $display = $f === $format ? 'block' : 'none';
                    echo "<div id='format-$f' class='tab-content' style='display: $display'>";
                    
                    $content = $wiki->formatOutput($result, $f);
                    
                    if ($f === 'html') {
                        echo $content;
                    } else {
                        echo '<pre>' . htmlspecialchars($content) . '</pre>';
                    }
                    
                    echo '</div>';
                }
                
                echo '</div>';
            }
            
        } catch (Exception $e) {
            echo '<div class="result error">';
            echo '<h3>❌ Error</h3>';
            echo '<p>' . htmlspecialchars($e->getMessage()) . '</p>';
            echo '</div>';
        }
    }
    ?>
    
    <script>
        function showFormat(format) {
            // Ocultar todas las pestañas
            document.querySelectorAll('.tab-content').forEach(content => {
                content.style.display = 'none';
            });
            
            document.querySelectorAll('.tab').forEach(tab => {
                tab.classList.remove('active');
            });
            
            // Mostrar la pestaña seleccionada
            document.getElementById('format-' + format).style.display = 'block';
            event.target.classList.add('active');
        }
    </script>
</body>
</html>