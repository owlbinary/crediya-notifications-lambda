
# Lambda Notificaciones

Este proyecto implementa una Lambda en Python 3.12 para procesar mensajes desde una cola SQS y enviar notificaciones por correo electrónico usando SES (arquitectura hexagonal).

## Requisitos
- Python 3.12 (recomendado usar conda)
- AWS CLI (opcional, para despliegue)

## Instalación y ambiente de desarrollo

### Usando conda
1. Crear el ambiente:
   ```bash
   conda env create -f environment.yml
   conda activate crediya-notification-lambda
   ```

### Usando pip
1. Instalar dependencias:
   ```bash
   pip install -r requirements.txt
   ```

## Variables de entorno
### Para procesamiento de notificaciones SQS/SES
- `SES_SOURCE_EMAIL`: Email verificado en SES desde el cual se enviarán las notificaciones.
- `AWS_REGION`: Región AWS (por defecto `us-east-1`).


## Ejecución local

### API REST
Puedes ejecutar la API localmente con Uvicorn:
```bash
uvicorn app.adapters.api:app --reload
```


## Pruebas y cobertura

### Ejecutar pruebas
Con el entorno activado, ejecuta:
```bash
pytest tests/
```

### Mostrar coverage
Para ver el reporte de cobertura en terminal:
```bash
pytest --cov=app --cov=lambda_handler --cov-report=term-missing tests/
```

Esto mostrará el porcentaje de líneas cubiertas y las líneas faltantes.

## Estructura del proyecto
- `app/domain/` - Lógica de dominio
- `app/application/` - Servicios y casos de uso
- `app/adapters/` - Adaptadores (API, etc)
- `app/infrastructure/` - Infraestructura (repositorios, logger)

## Arquitectura hexagonal y Clean Architecture
El proyecto sigue los principios de arquitectura hexagonal (puertos y adaptadores):

- **Puertos (interfaces)**: Definidos en `app/application/ports.py`. Permiten desacoplar la lógica de aplicación de los detalles de infraestructura.
- **Adaptadores de infraestructura**: Implementan los puertos para interactuar con servicios externos como AWS SQS y SES. Ejemplo:
   - `app/infrastructure/sqs_listener_adapter.py`: Adaptador para escuchar mensajes de SQS.
   - `app/infrastructure/ses_notification_adapter.py`: Adaptador para enviar notificaciones por SES.
- **Servicios de aplicación**: Orquestan los casos de uso y dependen solo de los puertos, nunca de implementaciones concretas.



## Caso de uso: Notificaciones parametrizables (SQS/SES y API)

La lambda puede ser configurada con un trigger SQS o invocada vía API REST. El mensaje de notificación es parametrizable y reutilizable según el tipo de notificación.

### Ejemplo de payload esperado (SQS o API)
El mensaje debe ser un JSON con la siguiente estructura:
```json
{
   "tipo": "estado_solicitud",
   "params": {
      "solicitudId": "123",
      "estado": "APROBADO",
      "justificacion": "Validación automática",
      "email": "usuario@correo.com"
   }
}
```

Puedes agregar nuevos tipos de notificación y sus parámetros en el `NotificationFactory`.

### Flujo resumido
1. SQS recibe un mensaje (por ejemplo, desde otro microservicio) o se invoca el endpoint `/api/v1/notificar`.
2. Lambda es invocada por el trigger SQS o por HTTP.
3. El handler o endpoint construye el mensaje usando `NotificationMessage` y `NotificationFactory` según el tipo.
4. SES envía el correo electrónico a los destinatarios configurados en el topic.