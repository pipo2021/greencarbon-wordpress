<?php
/**
 * Tema Green Carbon Bolivia.
 *
 * Todo el contenido vive en el Personalizador (Apariencia → Personalizar → Contenido de la web).
 * Los campos y sus valores predeterminados están en inc/campos.json, que genera
 * herramientas/convertir.py a partir del index.html original.
 */

defined( 'ABSPATH' ) || exit;

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

function gc_retrato( $k ) {
	$v = gc_valor( $k );
	echo '<div class="retrato">' . ( $v
		? '<img src="' . esc_url( $v ) . '" alt="" loading="lazy">'
		: '<svg class="i"><use href="#i-retrato"/></svg>' ) . '</div>';
}

function gc_oculto( $k ) {
	if ( ! gc_valor_es( $k ) ) {
		echo ' hidden';
	}
}

add_filter( 'show_admin_bar', '__return_false' ); // la barra tapa la cabecera fija del diseño

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
