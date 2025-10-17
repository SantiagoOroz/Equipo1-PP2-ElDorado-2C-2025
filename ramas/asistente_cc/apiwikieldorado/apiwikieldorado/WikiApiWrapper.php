<?php

class WikiApiWrapper {
    private $baseUrl;
    private $username;
    private $password;
    private $cookieFile;
    private $isLoggedIn = false;
    
    public function __construct($baseUrl, $username, $password) {
        $this->baseUrl = rtrim($baseUrl, '/');
        $this->username = $username;
        $this->password = $password;
        $this->cookieFile = tempnam(sys_get_temp_dir(), 'wiki_cookies_');
    }
    
    /**
     * Hacer login en la API de MediaWiki
     */
    public function login() {
        // Paso 1: Obtener token de login
        $tokenUrl = $this->baseUrl . '/api.php?action=query&meta=tokens&type=login&format=json';
        $tokenResponse = $this->makeRequest($tokenUrl, 'GET');
        
        if (!$tokenResponse) {
            throw new Exception('Error obteniendo token de login');
        }
        
        $tokenData = json_decode($tokenResponse, true);
        $loginToken = $tokenData['query']['tokens']['logintoken'];
        
        // Paso 2: Hacer login con el token
        $loginUrl = $this->baseUrl . '/api.php';
        $loginData = [
            'action' => 'login',
            'lgname' => $this->username,
            'lgpassword' => $this->password,
            'lgtoken' => $loginToken,
            'format' => 'json'
        ];
        
        $loginResponse = $this->makeRequest($loginUrl, 'POST', $loginData);
        $loginResult = json_decode($loginResponse, true);
        
        if ($loginResult['login']['result'] === 'Success') {
            $this->isLoggedIn = true;
            return true;
        } else {
            throw new Exception('Error en login: ' . $loginResult['login']['result']);
        }
    }
    
    /**
     * Buscar páginas en la wiki
     */
    public function searchPages($query, $limit = 10) {
        $this->ensureLoggedIn();
        
        $url = $this->baseUrl . '/api.php?' . http_build_query([
            'action' => 'query',
            'list' => 'search',
            'srsearch' => $query,
            'srlimit' => $limit,
            'format' => 'json'
        ]);
        
        $response = $this->makeRequest($url, 'GET');
        return json_decode($response, true);
    }
    
    /**
     * Obtener todas las páginas
     */
    public function getAllPages($limit = 50) {
        $this->ensureLoggedIn();
        
        $url = $this->baseUrl . '/api.php?' . http_build_query([
            'action' => 'query',
            'list' => 'allpages',
            'aplimit' => $limit,
            'format' => 'json'
        ]);
        
        $response = $this->makeRequest($url, 'GET');
        return json_decode($response, true);
    }
    
    /**
     * Obtener contenido de una página específica
     */
    public function getPageContent($title) {
        $this->ensureLoggedIn();
        
        $url = $this->baseUrl . '/api.php?' . http_build_query([
            'action' => 'query',
            'prop' => 'revisions',
            'rvprop' => 'content',
            'titles' => $title,
            'format' => 'json'
        ]);
        
        $response = $this->makeRequest($url, 'GET');
        return json_decode($response, true);
    }
    
    /**
     * Obtener resumen de una página
     */
    public function getPageSummary($title) {
        $this->ensureLoggedIn();
        
        $url = $this->baseUrl . '/api.php?' . http_build_query([
            'action' => 'query',
            'prop' => 'extracts',
            'exintro' => true,
            'explaintext' => true,
            'titles' => $title,
            'format' => 'json'
        ]);
        
        $response = $this->makeRequest($url, 'GET');
        return json_decode($response, true);
    }
    
    /**
     * Formatear resultados en diferentes formatos
     */
    public function formatOutput($data, $format = 'json') {
        switch (strtolower($format)) {
            case 'json':
                return $this->formatAsJson($data);
            
            case 'html':
                return $this->formatAsHtml($data);
            
            case 'text':
                return $this->formatAsText($data);
            
            case 'markdown':
                return $this->formatAsMarkdown($data);
            
            default:
                return $this->formatAsJson($data);
        }
    }
    
    private function formatAsJson($data) {
        return json_encode($data, JSON_PRETTY_PRINT | JSON_UNESCAPED_UNICODE);
    }
    
    private function formatAsHtml($data) {
        $html = "<div class='wiki-results'>";
        
        if (isset($data['query']['search'])) {
            $html .= "<h3>Resultados de búsqueda:</h3><ul>";
            foreach ($data['query']['search'] as $page) {
                $html .= "<li><strong>{$page['title']}</strong><br>";
                $html .= "<small>{$page['snippet']}</small></li>";
            }
            $html .= "</ul>";
        }
        
        if (isset($data['query']['allpages'])) {
            $html .= "<h3>Todas las páginas:</h3><ul>";
            foreach ($data['query']['allpages'] as $page) {
                $html .= "<li>{$page['title']}</li>";
            }
            $html .= "</ul>";
        }
        
        if (isset($data['query']['pages'])) {
            foreach ($data['query']['pages'] as $page) {
                $html .= "<h3>{$page['title']}</h3>";
                if (isset($page['revisions'][0]['*'])) {
                    $content = htmlspecialchars($page['revisions'][0]['*']);
                    $html .= "<div class='content'><pre>$content</pre></div>";
                }
                if (isset($page['extract'])) {
                    $html .= "<div class='extract'>{$page['extract']}</div>";
                }
            }
        }
        
        $html .= "</div>";
        return $html;
    }
    
    private function formatAsText($data) {
        $text = "";
        
        if (isset($data['query']['search'])) {
            $text .= "RESULTADOS DE BÚSQUEDA:\n" . str_repeat("=", 30) . "\n";
            foreach ($data['query']['search'] as $page) {
                $text .= "• {$page['title']}\n";
                $text .= "  " . strip_tags($page['snippet']) . "\n\n";
            }
        }
        
        if (isset($data['query']['allpages'])) {
            $text .= "TODAS LAS PÁGINAS:\n" . str_repeat("=", 20) . "\n";
            foreach ($data['query']['allpages'] as $page) {
                $text .= "• {$page['title']}\n";
            }
        }
        
        if (isset($data['query']['pages'])) {
            foreach ($data['query']['pages'] as $page) {
                $text .= strtoupper($page['title']) . "\n";
                $text .= str_repeat("=", strlen($page['title'])) . "\n\n";
                
                if (isset($page['revisions'][0]['*'])) {
                    $text .= $page['revisions'][0]['*'] . "\n\n";
                }
                if (isset($page['extract'])) {
                    $text .= $page['extract'] . "\n\n";
                }
            }
        }
        
        return $text;
    }
    
    private function formatAsMarkdown($data) {
        $markdown = "";
        
        if (isset($data['query']['search'])) {
            $markdown .= "## Resultados de búsqueda\n\n";
            foreach ($data['query']['search'] as $page) {
                $markdown .= "### {$page['title']}\n\n";
                $markdown .= strip_tags($page['snippet']) . "\n\n";
            }
        }
        
        if (isset($data['query']['allpages'])) {
            $markdown .= "## Todas las páginas\n\n";
            foreach ($data['query']['allpages'] as $page) {
                $markdown .= "- {$page['title']}\n";
            }
            $markdown .= "\n";
        }
        
        if (isset($data['query']['pages'])) {
            foreach ($data['query']['pages'] as $page) {
                $markdown .= "# {$page['title']}\n\n";
                
                if (isset($page['revisions'][0]['*'])) {
                    $markdown .= "```\n{$page['revisions'][0]['*']}\n```\n\n";
                }
                if (isset($page['extract'])) {
                    $markdown .= "{$page['extract']}\n\n";
                }
            }
        }
        
        return $markdown;
    }
    
    private function makeRequest($url, $method = 'GET', $data = null) {
        $ch = curl_init();
        
        curl_setopt_array($ch, [
            CURLOPT_URL => $url,
            CURLOPT_RETURNTRANSFER => true,
            CURLOPT_COOKIEFILE => $this->cookieFile,
            CURLOPT_COOKIEJAR => $this->cookieFile,
            CURLOPT_USERAGENT => 'WikiApiWrapper/1.0',
            CURLOPT_FOLLOWLOCATION => true,
            CURLOPT_SSL_VERIFYPEER => false,
            CURLOPT_TIMEOUT => 30
        ]);
        
        if ($method === 'POST' && $data) {
            curl_setopt($ch, CURLOPT_POST, true);
            curl_setopt($ch, CURLOPT_POSTFIELDS, http_build_query($data));
        }
        
        $response = curl_exec($ch);
        $httpCode = curl_getinfo($ch, CURLINFO_HTTP_CODE);
        curl_close($ch);
        
        if ($httpCode !== 200) {
            throw new Exception("Error HTTP: $httpCode");
        }
        
        return $response;
    }
    
    private function ensureLoggedIn() {
        if (!$this->isLoggedIn) {
            $this->login();
        }
    }
    
    public function __destruct() {
        if (file_exists($this->cookieFile)) {
            unlink($this->cookieFile);
        }
    }
}