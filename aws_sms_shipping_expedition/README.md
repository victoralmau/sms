Permite la posibilidad mediante shipping_expedition de enviar SMS de información de las expedición a los transportistas según los campos: send_sms_info y sms_info_sms_template_id

## Crones
### Shipping Expedition Sms Info
Frecuencia: 1 vez al día

Descripción: Revisa todas las expediciones de los transportistas que lo tienen definido que NO tengan definida fecha de envío sms y cuyo estado NO sea 'Error', 'Generado', 'Cancelado' y 'Entregado' para enviar el email automático al cliente
