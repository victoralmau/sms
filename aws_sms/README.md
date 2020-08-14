El módulo contiene el desarrollo que permite realizar el envío de SMS a través de AWS

## odoo.conf
- aws_access_key_id=xxx
- aws_secret_key_id=xxx
- aws_region_name=eu-west-1

## Parámetros de configuración
- sms_template_id_default_sale_order 

En el apartado Configuración > Técnico se añade la opción "SMS" con los siguientes elementos:

- SMS Mensajes
- SMS Plantillas

## Crones

### SMS USAGE REPORTS 
Frecuencia: 1 vez al día

Descripción: Se conecta al bucket de S3 donde están almacenados los reportes de SMS, se leen las líneas y se "actualiza" respecto a los SMS enviados previamente (estado de entrega, precio, numero de parte, partes totales). Siempre va con un día de retraso como mínimo ya que NO se guarda en S3 el reporte de hoy hasta mañana
