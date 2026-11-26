<?php
/**
 * Aviso de Privacidad del formulario de contacto (?privacidad). Texto entregado por el cliente; solo en español.
 */

defined( 'ABSPATH' ) || exit;
?>
<!doctype html>
<html lang="es">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
<title>Aviso de Privacidad · <?php gc_t( 'gen_titulo' ); ?></title>
<meta name="robots" content="noindex">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Barlow+Condensed:wght@300;400;500;600;700;800&family=Barlow:wght@400;500;600;700&family=Barlow+Semi+Condensed:wght@400;500&display=swap">
<?php wp_head(); ?>
<style>
.aviso { max-width: 760px; margin: 0 auto; padding: 72px 20px 96px; }
.aviso h1 { font-size: clamp(32px, 5vw, 48px); margin-bottom: 4px; }
.aviso h2 { font-size: 22px; margin: 36px 0 8px; }
.aviso p { margin: 0 0 14px; }
.aviso a { color: inherit; }
.aviso .volver { display: inline-block; margin-bottom: 32px; }
</style>
</head>
<body>
<?php wp_body_open(); ?>
<main class="aviso">
  <a class="volver" href="<?php echo esc_url( home_url( '/' ) ); ?>">← Volver al sitio</a>
  <h1>Aviso de Privacidad del Formulario de Contacto</h1>
  <p>Green Carbon Bolivia S.R.L.</p>

  <h2>1. Responsable del tratamiento</h2>
  <p>Green Carbon Bolivia S.R.L., con domicilio en el Edificio Manzana 40, piso 17, oficina 1710, Santa Cruz de la Sierra, Bolivia, es responsable del tratamiento de los datos personales recabados mediante el formulario de contacto de su sitio web. Las consultas sobre este Aviso podrán dirigirse a <a href="mailto:info@greencarbonbolivia.com">info@greencarbonbolivia.com</a>.</p>

  <h2>2. Datos y finalidad del tratamiento</h2>
  <p>Trataremos los datos de identificación y contacto que usted proporcione, el contenido de su mensaje y las comunicaciones posteriores vinculadas con su solicitud. Utilizaremos esta información para recibir, registrar, canalizar, responder y dar seguimiento a su consulta, así como para conservar constancia de su atención durante el plazo indicado en este Aviso.</p>
  <p>El uso de estos datos para fines publicitarios requerirá un consentimiento específico. Le solicitamos proporcionar únicamente la información necesaria para atender su consulta.</p>

  <h2>3. Consentimiento</h2>
  <p>En el marco del artículo 56 del Decreto Supremo N.º 1793, usted podrá manifestar su consentimiento expreso antes de enviar el formulario marcando la casilla habilitada junto al enlace a este Aviso. Si prefiere comunicarse por otra vía, puede escribir al correo institucional indicado en el numeral 1.</p>

  <h2>4. Acceso a los datos y medidas de seguridad</h2>
  <p>El acceso se limitará al personal expresamente autorizado para gestionar el canal de contacto y, cuando la consulta lo requiera, al personal del área que deba intervenir en su atención. Cada persona accederá únicamente a la información necesaria para cumplir su función y estará sujeta a deberes de confidencialidad.</p>
  <p>Cuando intervengan proveedores de alojamiento web, correo electrónico o gestión del formulario, deberán tratar los datos conforme a instrucciones documentadas de Green Carbon Bolivia S.R.L. y bajo obligaciones de confidencialidad y seguridad. La comunicación o transferencia de datos a terceros requerirá el consentimiento previo de su titular u orden escrita de autoridad judicial competente, conforme a la normativa aplicable.</p>
  <p>Green Carbon Bolivia S.R.L. aplicará medidas técnicas y organizativas para prevenir el acceso, uso, alteración, pérdida o divulgación no autorizados de la información.</p>

  <h2>5. Plazo de conservación</h2>
  <p>Los datos personales se conservarán durante cinco (5) años, contados desde la última comunicación relacionada con la consulta. Vencido ese plazo, se eliminarán de forma segura o se anonimizarán de manera irreversible.</p>
  <p>Si una obligación legal, una orden judicial o un procedimiento en curso exige conservar determinada información por más tiempo, se mantendrá únicamente la información necesaria, con acceso restringido, hasta que cese la causa que justifique su conservación. El plazo se aplicará sin perjuicio de las solicitudes de cancelación que correspondan conforme a la normativa aplicable.</p>

  <h2>6. Derechos del titular</h2>
  <p>Usted podrá solicitar el acceso a sus datos, su rectificación, actualización o cancelación, objetar su tratamiento o solicitar la revocación del consentimiento cuando exista causa justificada. La revocación surtirá efectos hacia el futuro.</p>
  <p>Para ejercer estos derechos, escriba a <a href="mailto:info@greencarbonbolivia.com">info@greencarbonbolivia.com</a> con el asunto «Privacidad – Ejercicio de derechos» e indique qué solicita. Cuando sea necesario, la empresa verificará su identidad o la representación de quien actúe en su nombre, solicitando solo la información indispensable para esa verificación.</p>

  <h2>7. Legislación aplicable y solución de controversias</h2>
  <p>Este Aviso se rige por la legislación del Estado Plurinacional de Bolivia. Toda controversia derivada de su aplicación que sea legalmente susceptible de arbitraje se resolverá, cuando las partes lo hayan convenido por escrito, mediante arbitraje institucional en derecho administrado por el Centro de Conciliación y Arbitraje de CAINCO, conforme a la Ley N.º 708 y al Reglamento de Procedimiento Arbitral del Centro. La sede será Santa Cruz de la Sierra, Bolivia, y el idioma será el castellano.</p>
  <p>Queda a salvo el derecho del titular a interponer la Acción de Protección de Privacidad prevista en los artículos 130 y 131 de la Constitución Política del Estado, acudir a las autoridades competentes y ejercer los demás derechos y recursos irrenunciables previstos por ley.</p>
</main>
<?php wp_footer(); ?>
</body>
</html>
