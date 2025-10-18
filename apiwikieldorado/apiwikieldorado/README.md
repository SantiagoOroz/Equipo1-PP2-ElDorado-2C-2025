# 🔧 Wiki API Wrapper - El Dorado

Un wrapper PHP para facilitar el acceso de solo lectura a la API de MediaWiki de El Dorado.

## 📋 Características

- ✅ **Autenticación automática** con usuario dedicado API
- 🔍 **Búsqueda de páginas** con términos específicos
- 📋 **Listado completo** de todas las páginas
- 📄 **Extracción de contenido** completo de páginas
- 📊 **Múltiples formatos** de salida: JSON, HTML, Texto, Markdown
- 🛡️ **Solo lectura** - Sin capacidad de modificación
- 🌐 **Interfaz web** incluida para pruebas

## 🚀 Instalación

1. Clona o descarga los archivos:
```bash
git clone [este-repositorio]
# o descarga directamente los archivos
```

2. Asegúrate de tener PHP con cURL habilitado:
```bash
php -m | grep curl
```

## 📁 Archivos incluidos

- `WikiApiWrapper.php` - Clase principal del wrapper
- `ejemplo.php` - Script de línea de comandos para pruebas
- `web.php` - Interfaz web para pruebas interactivas
- `README.md` - Esta documentación

## 💻 Uso por línea de comandos

```bash
php ejemplo.php
```

Este script ejecutará automáticamente varios ejemplos de uso:
- Búsqueda por término
- Listado de páginas
- Extracción de contenido específico
- Muestra de diferentes formatos

## 🌐 Uso desde interfaz web

1. Inicia un servidor web local:
```bash
php -S localhost:8000
```

2. Abre tu navegador en: `http://localhost:8000/web.php`

3. Usa la interfaz para:
   - Buscar páginas por términos
   - Listar todas las páginas
   - Obtener contenido completo
   - Ver resultados en diferentes formatos

## 🔨 Uso programático

```php
<?php
require_once 'WikiApiWrapper.php';

// Configurar conexión
$wiki = new WikiApiWrapper(
    'https://objetivos.eldoradosrl.ar/wiki',
    'Userapi',
    'pr0y3ct0llm'
);

// Login automático
$wiki->login();

// Buscar páginas
$results = $wiki->searchPages('hormigón', 5);

// Obtener contenido específico
$content = $wiki->getPageContent('ACH 01 - Verificación de equipos e instrumentos');

// Formatear resultado
echo $wiki->formatOutput($results, 'json');
echo $wiki->formatOutput($content, 'html');
```

## 📚 Métodos disponibles

### `login()`
Autentica con el usuario API. Se ejecuta automáticamente cuando es necesario.

### `searchPages($query, $limit = 10)`
Busca páginas que contengan el término especificado.

**Parámetros:**
- `$query` (string): Término de búsqueda
- `$limit` (int): Número máximo de resultados (1-100)

### `getAllPages($limit = 50)`
Obtiene una lista de todas las páginas de la wiki.

**Parámetros:**
- `$limit` (int): Número máximo de páginas (1-100)

### `getPageContent($title)`
Extrae el contenido completo (wikitext) de una página específica.

**Parámetros:**
- `$title` (string): Título exacto de la página

### `getPageSummary($title)`
Obtiene un resumen en texto plano de una página.

**Parámetros:**
- `$title` (string): Título exacto de la página

### `formatOutput($data, $format = 'json')`
Formatea los datos de respuesta en el formato especificado.

**Formatos disponibles:**
- `json` - JSON formateado y legible
- `html` - HTML estructurado con CSS
- `text` - Texto plano organizado
- `markdown` - Formato Markdown

## 🛡️ Seguridad

- **Usuario dedicado**: Utiliza credenciales específicas para API
- **Solo lectura**: Sin permisos de escritura/modificación
- **Rate limiting**: Respeta límites del servidor
- **Manejo de errores**: Captura y reporta errores apropiadamente

## ⚠️ Consideraciones

- El usuario API debe existir y tener permisos de lectura
- Requiere conexión a internet para acceder a la API
- Los archivos de cookies se crean temporalmente y se eliminan automáticamente
- Respeta los límites de velocidad del servidor MediaWiki

## 🔧 Configuración

Para usar con otra instalación de MediaWiki, modifica las credenciales en los archivos:

```php
$wikiUrl = 'https://tu-wiki.com/wiki';
$username = 'tu-usuario-api';
$password = 'tu-password-api';
```

## 📖 Ejemplos de resultados

### Búsqueda en formato texto:
```
RESULTADOS DE BÚSQUEDA:
==============================
• Laboratorista de hormigón
  Rol: Laboratorista de hormigón | Área: Calidad...

• PPH 03 - Producción del hormigón
  ...procedimiento es implementar una metodología...
```

### Contenido en formato JSON:
```json
{
    "query": {
        "pages": {
            "123": {
                "title": "ACH 01 - Verificación de equipos",
                "revisions": [{
                    "*": "Se utiliza para documentar el proceso..."
                }]
            }
        }
    }
}
```

## 📞 Soporte

Para reportar problemas o solicitar funcionalidades, contacta al administrador del sistema.

---

**Desarrollado para El Dorado S.R.L.** 🏗️