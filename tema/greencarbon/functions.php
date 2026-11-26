<?php
/**
 * Tema Green Carbon Bolivia.
 *
 * Todo el contenido vive en el Personalizador (Apariencia → Personalizar → Contenido de la web).
 * Los campos y sus valores predeterminados están en inc/campos.json, que genera
 * herramientas/convertir.py a partir del index.html original.
 */

defined( 'ABSPATH' ) || exit;

const GC_RECORRIDO_V = '7'; // sube al cambiar pack/v: invalida la caché del recorrido

const GC_INLINE = array(
	'em'     => array(),
	'strong' => array(),
	'b'      => array(),
	'br'     => array(),
	'a'      => array( 'href' => array(), 'target' => array(), 'rel' => array() ),
);

function gc_secciones() {
	static $s;
	return $s ??= json_decode( file_get_contents( __DIR__ . '/inc/campos.json' ), true );
}

function gc_campo( $k ) {
	static $i;
	if ( null === $i ) {
		$i = array();
		foreach ( gc_secciones() as $s ) {
			$i += $s['campos'];
		}
	}
	return $i[ $k ];
}

/** Rutas relativas del tema (assets/…) a URL absoluta; URLs externas o subidas quedan igual. */
function gc_resolver( $u ) {
	return ( '' === $u || preg_match( '#^([a-z]+:|/)#i', $u ) ) ? $u : get_theme_file_uri( $u );
}

function gc_defecto( $k ) {
	$c = gc_campo( $k );
	return in_array( $c['tipo'], array( 'imagen', 'video', 'url' ), true ) ? gc_resolver( $c['defecto'] ) : $c['defecto'];
}

/** Idioma de la página: ?lang=en para inglés; español por defecto. */
function gc_lang() {
	return ( isset( $_GET['lang'] ) && 'en' === $_GET['lang'] && gc_valor_es( 'mostrar_idioma' ) ) ? 'en' : 'es'; // phpcs:ignore WordPress.Security.NonceVerification
}

function gc_valor_es( $k ) {
	return get_theme_mod( $k, gc_defecto( $k ) );
}

/** En inglés, los textos usan su campo _en; si está vacío se muestra el español. */
function gc_valor( $k ) {
	$c = gc_campo( $k );
	if ( 'en' === gc_lang() && isset( $c['en'] ) ) {
		$v = get_theme_mod( $k . '_en', $c['en'] );
		if ( '' !== trim( (string) $v ) ) {
			return $v;
		}
	}
	return gc_valor_es( $k );
}

function gc_url_idioma( $lang ) {
	return 'en' === $lang ? add_query_arg( 'lang', 'en', home_url( '/' ) ) : home_url( '/' );
}

function gc_idioma() {
	if ( ! gc_valor_es( 'mostrar_idioma' ) ) {
		return;
	}
	echo '<nav class="idioma" aria-label="' . ( 'en' === gc_lang() ? 'Language' : 'Idioma' ) . '">';
	foreach ( array( 'es' => 'ES', 'en' => 'EN' ) as $l => $txt ) {
		printf(
			'<a href="%s" hreflang="%s" lang="%s"%s>%s</a>',
			esc_url( gc_url_idioma( $l ) ),
			$l,
			$l,
			gc_lang() === $l ? ' aria-current="true"' : '',
			$txt
		);
	}
	echo '</nav>';
}

function gc_hreflang() {
	if ( ! gc_valor_es( 'mostrar_idioma' ) ) {
		return;
	}
	foreach ( array( 'es', 'en' ) as $l ) {
		printf( '<link rel="alternate" hreflang="%s" href="%s">' . "\n", $l, esc_url( gc_url_idioma( $l ) ) );
	}
	printf( '<link rel="alternate" hreflang="x-default" href="%s">' . "\n", esc_url( gc_url_idioma( 'es' ) ) );
}

function gc_t( $k ) {
	echo wp_kses( gc_valor( $k ), GC_INLINE );
}

function gc_a( $k ) {
	echo esc_attr( wp_strip_all_tags( gc_valor( $k ) ) );
}

function gc_u( $k ) {
	echo esc_url( gc_valor( $k ) );
}

/** El srcset original solo vale mientras la imagen sea la predeterminada. */
function gc_srcset( $k_imagen, $srcset ) {
	if ( gc_valor( $k_imagen ) !== gc_defecto( $k_imagen ) ) {
		return;
	}
	$partes = array_map(
		function ( $p ) {
			$p = explode( ' ', trim( $p ), 2 );
			return gc_resolver( $p[0] ) . ( isset( $p[1] ) ? ' ' . $p[1] : '' );
		},
		explode( ',', $srcset )
	);
	echo ' srcset="' . esc_attr( implode( ', ', $partes ) ) . '"';
}

/** Dato real si el admin lo cargó; si no, el aviso amarillo/naranja del diseño. */
function gc_aviso( $k, $clase, $texto, $texto_en = '' ) {
	$v = gc_valor( $k );
	if ( '' !== trim( (string) $v ) ) {
		echo wp_kses( $v, GC_INLINE );
	} else {
		echo '<span class="' . esc_attr( $clase ) . '">' . esc_html( 'en' === gc_lang() && $texto_en ? $texto_en : $texto ) . '</span>';
	}
}

function gc_foto_o_aviso( $k, $texto, $texto_en = '' ) {
	$v = gc_valor( $k );
	if ( $v ) {
		echo '<img src="' . esc_url( $v ) . '" alt="" loading="lazy">';
	} else {
		echo '<span class="pend">' . esc_html( 'en' === gc_lang() && $texto_en ? $texto_en : $texto ) . '</span>';
	}
}

/** Imagen estática del mapa: solo se imprime si el admin la cargó (el CSS oculta entonces el aviso). */
function gc_mapa_img( $k, $k_alt ) {
	$v = gc_valor( $k );
	if ( $v ) {
		echo '<img class="mapa-img" src="' . esc_url( $v ) . '" alt="' . esc_attr( wp_strip_all_tags( gc_valor( $k_alt ) ) ) . '" loading="lazy">';
	}
}

/** Ancho y alto solo mientras la imagen sea la predeterminada (evita saltos de diseño). */
function gc_medidas( $k, $w, $h ) {
	if ( gc_valor( $k ) === gc_defecto( $k ) ) {
		printf( ' width="%d" height="%d"', $w, $h );
	}
}

function gc_retrato( $k ) {
	$v = gc_valor( $k );
	ob_start();
	gc_medidas( $k, 640, 800 );
	echo '<div class="retrato">' . ( $v
		? '<img src="' . esc_url( $v ) . '"' . ob_get_clean() . ' alt="" loading="lazy" decoding="async">'
		: '<svg class="i"><use href="#i-retrato"/></svg>' ) . '</div>';
}

function gc_oculto( $k ) {
	if ( ! gc_valor_es( $k ) ) {
		echo ' hidden';
	}
}

// ?privacidad muestra el Aviso de Privacidad que enlaza la casilla de consentimiento del formulario.
add_action(
	'template_redirect',
	function () {
		if ( ! isset( $_GET['privacidad'] ) ) { // phpcs:ignore WordPress.Security.NonceVerification
			return;
		}
		add_action( 'wp_enqueue_scripts', fn() => wp_dequeue_script( 'greencarbon' ), 20 ); // main.js espera la portada
		include __DIR__ . '/privacidad.php';
		exit;
	}
);

add_filter( 'show_admin_bar', '__return_false' ); // la barra tapa la cabecera fija del diseño

// El menú se edita como texto en «Cabecera y menú»: el panel de menús de WordPress no aplica (se registra con prioridad 11).
add_action(
	'customize_register',
	function ( WP_Customize_Manager $wp ) {
		$wp->remove_panel( 'nav_menus' );
	},
	20
);

// El tema no tiene áreas de widgets: sin esto el núcleo imprime la plantilla del panel inexistente y avisa en el log.
add_action(
	'customize_register',
	function ( WP_Customize_Manager $wp ) {
		if ( $wp->widgets ) {
			remove_action( 'customize_controls_print_footer_scripts', array( $wp->widgets, 'output_widget_control_templates' ) );
		}
	}
);

add_action(
	'wp_enqueue_scripts',
	function () {
		$v = wp_get_theme()->get( 'Version' );
		wp_enqueue_style( 'greencarbon', get_stylesheet_uri(), array(), $v );
		$alfas = '';
		foreach ( array( 'alfa-hoja', 'alfa-oscuro', 'alfa-tarjeta' ) as $k ) {
			$alfas .= '--' . $k . ':' . gc_limpiar_opacidad( gc_valor_es( $k ) ) . ';';
		}
		wp_add_inline_style( 'greencarbon', ':root{' . $alfas . '}' );
		wp_enqueue_script( 'greencarbon', get_theme_file_uri( 'js/main.js' ), array(), $v, true );
		$gc = array(
			'tema'    => untrailingslashit( get_template_directory_uri() ),
			'v'       => GC_RECORRIDO_V,
			'enlaces' => array(
				'mapas'     => gc_valor( 'enlace_mapas' ),
				'incendios' => gc_valor( 'enlace_incendios' ),
			),
			't'       => array(),
		);
		foreach ( gc_secciones() as $s ) {
			if ( 'js' === $s['id'] ) {
				foreach ( array_keys( $s['campos'] ) as $k ) {
					$gc['t'][ substr( $k, 3 ) ] = wp_strip_all_tags( gc_valor( $k ) );
				}
			}
		}
		wp_add_inline_script( 'greencarbon', 'window.GC = ' . wp_json_encode( $gc ) . ';', 'before' );
	}
);

add_action(
	'customize_register',
	function ( WP_Customize_Manager $wp ) {
		$wp->add_panel(
			'gc_contenido',
			array(
				'title'       => 'Contenido de la web',
				'description' => 'Cada sección de la página tiene sus textos, fotos y enlaces. Vaciar un aviso («Falta», «SSOT») lo vuelve a mostrar.',
				'priority'    => 1,
			)
		);
		foreach ( gc_secciones() as $n => $s ) {
			$sid = 'gc_' . $s['id'];
			$wp->add_section( $sid, array( 'title' => $s['titulo'], 'panel' => 'gc_contenido', 'priority' => $n ) );
			foreach ( $s['campos'] as $k => $c ) {
				$tipo = $c['tipo'];
				$wp->add_setting(
					$k,
					array(
						'default'           => gc_defecto( $k ),
						'sanitize_callback' => array(
							'texto'   => 'gc_limpiar_texto',
							'parrafo' => 'gc_limpiar_texto',
							'check'   => 'wp_validate_boolean',
							'opacidad' => 'gc_limpiar_opacidad',
						)[ $tipo ] ?? 'esc_url_raw',
					)
				);
				$args = array(
					'label'       => ( isset( $c['en'] ) ? 'ES · ' : '' ) . $c['etiqueta'],
					'description' => $c['desc'],
					'section'     => $sid,
				);
				if ( 'imagen' === $tipo ) {
					$wp->add_control( new WP_Customize_Image_Control( $wp, $k, $args ) );
				} elseif ( 'video' === $tipo ) {
					$wp->add_control( new WP_Customize_Upload_Control( $wp, $k, $args + array( 'mime_type' => 'video' ) ) );
				} else {
					$args['type'] = array(
						'texto'   => 'text',
						'parrafo' => 'textarea',
						'url'     => 'url',
						'check'   => 'checkbox',
						'opacidad' => 'range',
					)[ $tipo ];
					if ( 'opacidad' === $tipo ) {
						$args['input_attrs'] = array( 'min' => 0.3, 'max' => 1, 'step' => 0.02 );
					}
					$wp->add_control( $k, $args );
				}
				if ( isset( $c['en'] ) ) {
					$wp->add_setting(
						$k . '_en',
						array(
							'default'           => $c['en'],
							'sanitize_callback' => 'gc_limpiar_texto',
						)
					);
					$wp->add_control(
						$k . '_en',
						array(
							'label'       => 'EN · ' . $c['etiqueta'],
							'description' => 'Inglés. Vacío = se muestra el español.',
							'section'     => $sid,
							'type'        => $args['type'],
						)
					);
				}
			}
		}
		// Del tema por defecto: el sitio es una sola página, estas secciones no aplican.
		foreach ( array( 'static_front_page', 'custom_css' ) as $quitar ) {
			$wp->remove_section( $quitar );
		}
	}
);

function gc_limpiar_opacidad( $v ) {
	return round( min( 1, max( 0.3, (float) $v ) ), 2 );
}

function gc_limpiar_texto( $v ) {
	return wp_kses( $v, GC_INLINE );
}

// Precargas, canónica, Open Graph, Twitter y JSON-LD (antes que los estilos del núcleo).
add_action(
	'wp_head',
	function () {
		$t   = fn( $f ) => esc_url( get_theme_file_uri( $f ) );
		$en  = 'en' === gc_lang();
		$url = gc_url_idioma( gc_lang() );
		$tit = wp_strip_all_tags( gc_valor( 'gen_titulo' ) );
		$des = wp_strip_all_tags( gc_valor( 'gen_descripcion' ) );
		$img = get_theme_file_uri( 'assets/compartir.jpg' );
		foreach ( array( 'inter-tight-latin', 'inter-latin' ) as $f ) {
			echo '<link rel="preload" href="' . $t( "fonts/$f.woff2" ) . '" as="font" type="font/woff2" crossorigin>' . "\n";
		}
		echo '<link rel="preload" href="' . $t( 'assets/logo-white.webp' ) . '" as="image" fetchpriority="high">' . "\n";
		echo '<link rel="preload" href="' . $t( 'pack/v/manifest.json' ) . '?v=' . GC_RECORRIDO_V . '" as="fetch" crossorigin media="(max-aspect-ratio: 1/1)">' . "\n";
		echo '<link rel="canonical" href="' . esc_url( $url ) . '">' . "\n";
		echo '<meta name="theme-color" content="#0a1712">' . "\n";
		$meta = array(
			'og:type'             => 'website',
			'og:site_name'        => 'Green Carbon Bolivia',
			'og:title'            => $tit,
			'og:description'      => $des,
			'og:url'              => $url,
			'og:locale'           => $en ? 'en_US' : 'es_LA',
			'og:locale:alternate' => $en ? 'es_LA' : 'en_US',
			'og:image'            => $img,
			'og:image:width'      => '1200',
			'og:image:height'     => '630',
			'og:image:alt'        => wp_strip_all_tags( gc_valor( 's04_02' ) ),
		);
		foreach ( $meta as $p => $c ) {
			echo '<meta property="' . $p . '" content="' . esc_attr( $c ) . '">' . "\n";
		}
		foreach ( array( 'card' => 'summary_large_image', 'title' => $tit, 'description' => $des, 'image' => $img ) as $n => $c ) {
			echo '<meta name="twitter:' . $n . '" content="' . esc_attr( $c ) . '">' . "\n";
		}
		$home   = gc_url_idioma( 'es' );
		$correo = 'info@greencarbonbolivia.com';
		$ld     = array(
			'@context' => 'https://schema.org',
			'@graph'   => array(
				array(
					'@type'        => 'Organization',
					'@id'          => $home . '#organizacion',
					'name'         => 'Green Carbon Bolivia',
					'url'          => $home,
					'description'  => $des,
					'logo'         => get_theme_file_uri( 'apple-touch-icon.png' ),
					'sameAs'       => array_values( array_filter( array( gc_valor( 'pie_18' ), gc_valor( 'pie_20' ), gc_valor( 'pie_22' ) ) ) ),
					'email'        => $correo,
					'address'      => array(
						'@type'           => 'PostalAddress',
						'streetAddress'   => 'Edificio Manzana 40, piso 17, oficina 1710',
						'addressLocality' => 'Santa Cruz de la Sierra',
						'addressCountry'  => 'BO',
					),
					'contactPoint' => array(
						array(
							'@type'             => 'ContactPoint',
							'contactType'       => 'customer support',
							'telephone'         => '+591-75005342',
							'email'             => $correo,
							'areaServed'        => 'BO',
							'availableLanguage' => array( 'es', 'en' ),
						),
					),
				),
				array(
					'@type'      => 'WebSite',
					'@id'        => $home . '#sitio',
					'url'        => $home,
					'name'       => 'Green Carbon Bolivia',
					'inLanguage' => array( 'es', 'en' ),
					'publisher'  => array( '@id' => $home . '#organizacion' ),
				),
				array(
					'@type'              => 'WebPage',
					'@id'                => $url . '#pagina',
					'url'                => $url,
					'name'               => $tit,
					'description'        => $des,
					'inLanguage'         => $en ? 'en' : 'es',
					'isPartOf'           => array( '@id' => $home . '#sitio' ),
					'about'              => array( '@id' => $home . '#organizacion' ),
					'primaryImageOfPage' => array(
						'@type' => 'ImageObject',
						'url'   => $img,
					),
				),
			),
		);
		echo '<script type="application/ld+json">' . wp_json_encode( $ld, JSON_UNESCAPED_UNICODE ) . '</script>' . "\n";
		echo '<link rel="icon" href="' . $t( 'favicon.ico' ) . '" sizes="32x32">' . "\n";
		echo '<link rel="apple-touch-icon" href="' . $t( 'apple-touch-icon.png' ) . '">' . "\n";
	},
	2
);

/** Valida el envío del formulario. Devuelve los datos limpios o null. */
function gc_contacto_datos( array $p ) {
	if ( ! empty( $p['web'] ) ) {
		return array(); // trampa para bots: se responde ok sin enviar
	}
	$d = array(
		'nombre'  => sanitize_text_field( $p['nombre'] ?? '' ),
		'correo'  => sanitize_email( $p['correo'] ?? '' ),
		'mensaje' => sanitize_textarea_field( $p['mensaje'] ?? '' ),
	);
	if ( '' === $d['nombre'] || ! is_email( $d['correo'] ) || '' === $d['mensaje'] || empty( $p['consentimiento'] ) ) {
		return null;
	}
	foreach ( $p as $k => $v ) {
		if ( is_scalar( $v ) && ! isset( $d[ $k ] ) && ! in_array( $k, array( 'web', 'consentimiento' ), true ) ) {
			$d[ sanitize_key( $k ) ] = sanitize_text_field( (string) $v );
		}
	}
	return $d;
}

// Sin servicio externo (s18_09 vacío), el formulario envía aquí y WordPress manda el correo.
add_action(
	'rest_api_init',
	function () {
		register_rest_route(
			'gc/v1',
			'/contacto',
			array(
				'methods'             => 'POST',
				'permission_callback' => '__return_true',
				'callback'            => function ( WP_REST_Request $req ) {
					$d = gc_contacto_datos( (array) ( $req->get_json_params() ?: $req->get_body_params() ) );
					if ( null === $d ) {
						return new WP_REST_Response( array( 'ok' => false ), 400 );
					}
					if ( ! $d ) {
						return new WP_REST_Response( array( 'ok' => true ), 200 );
					}
					$para = sanitize_email( wp_strip_all_tags( gc_valor_es( 's18_06' ) ) ) ?: get_option( 'admin_email' );
					$txt  = '';
					foreach ( $d as $k => $v ) {
						$txt .= ucfirst( $k ) . ': ' . $v . "\n";
					}
					$ok = wp_mail( $para, 'Contacto web: ' . $d['nombre'], $txt, array( 'Reply-To: ' . $d['nombre'] . ' <' . $d['correo'] . '>' ) );
					return new WP_REST_Response( array( 'ok' => $ok ), $ok ? 200 : 500 );
				},
			)
		);
	}
);
