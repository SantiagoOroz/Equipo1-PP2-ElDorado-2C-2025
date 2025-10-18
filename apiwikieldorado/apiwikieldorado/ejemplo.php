<?php

require_once 'WikiApiWrapper.php';

try {
    // Configuración
    $wikiUrl = 'https://objetivos.eldoradosrl.ar/wiki';
    $username = 'Userapi';
    $password = 'pr0y3ct0llm';
    
    // Crear instancia del wrapper
    echo "🔧 Iniciando conexión con la API de MediaWiki...\n";
    $wiki = new WikiApiWrapper($wikiUrl, $username, $password);
    
    // Hacer login
    echo "🔑 Haciendo login...\n";
    $wiki->login();
    echo "✅ Login exitoso!\n\n";
    
    // === EJEMPLOS DE USO ===
    
    // 1. Buscar páginas
    echo "🔍 Buscando páginas con 'hormigón'...\n";
    $searchResults = $wiki->searchPages('hormigón', 5);
    echo $wiki->formatOutput($searchResults, 'text');
    echo "\n" . str_repeat("-", 50) . "\n\n";
    
    // 2. Listar todas las páginas
    echo "📋 Listando primeras 10 páginas...\n";
    $allPages = $wiki->getAllPages(10);
    echo $wiki->formatOutput($allPages, 'text');
    echo "\n" . str_repeat("-", 50) . "\n\n";
    
    // 3. Obtener contenido específico
    echo "📄 Obteniendo contenido de una página específica...\n";
    $pageContent = $wiki->getPageContent('ACH 01 - Verificación de equipos e instrumentos');
    echo $wiki->formatOutput($pageContent, 'text');
    echo "\n" . str_repeat("-", 50) . "\n\n";
    
    // === EJEMPLOS EN DIFERENTES FORMATOS ===
    
    // Buscar algo para mostrar en diferentes formatos
    $searchData = $wiki->searchPages('ACH', 3);
    
    echo "📊 MISMO RESULTADO EN DIFERENTES FORMATOS:\n\n";
    
    // JSON
    echo "=== FORMATO JSON ===\n";
    echo $wiki->formatOutput($searchData, 'json');
    echo "\n\n";
    
    // HTML
    echo "=== FORMATO HTML ===\n";
    echo $wiki->formatOutput($searchData, 'html');
    echo "\n\n";
    
    // Markdown
    echo "=== FORMATO MARKDOWN ===\n";
    echo $wiki->formatOutput($searchData, 'markdown');
    echo "\n\n";
    
    echo "🎉 Prueba completada exitosamente!\n";
    
} catch (Exception $e) {
    echo "❌ Error: " . $e->getMessage() . "\n";
}