# =============================================================================
# TELEGRAM BOT CON GRÁFICAS - SISTEMA IA DE RIEGO SINALOA (VERSIÓN RÁPIDA)
# =============================================================================

import asyncio
import logging
import sys
import os
from datetime import datetime, timedelta
import io
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import re
import time
from functools import lru_cache
from telegram import Bot, Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes
import matplotlib
matplotlib.use('Agg')
plt.style.use('dark_background')

# Agregar paths
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'models'))

from models.recomendador import Recomendador
from config import PARCELAS, SUELO, CLASES_RIEGO

# =============================================================================
# CONFIGURACIÓN
# =============================================================================

TOKEN = "8900660488:AAGbtrEsoJ2b7i1l2434eOP9dAfqkGPUg9Q"

# Configuración de rendimiento
DPI_GRAFICAS = 60  # Reducido de 100 a 60 para más velocidad
TAMANO_FIGURA = (8, 4)  # Reducido de (10,6)
CACHE_TIEMPO_SEGUNDOS = 300  # 5 minutos de caché

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

recomendador = Recomendador()

# =============================================================================
# SISTEMA DE CACHÉ OPTIMIZADO
# =============================================================================

class CacheRapido:
    """Caché simple y rápido para datos del recomendador"""
    def __init__(self, ttl_segundos=300):
        self.cache = {}
        self.ttl = ttl_segundos
        self.tiempos = {}
    
    def get(self, key):
        """Obtener dato del caché si existe y no expiró"""
        if key in self.cache and key in self.tiempos:
            if (datetime.now() - self.tiempos[key]).seconds < self.ttl:
                return self.cache[key]
        return None
    
    def set(self, key, value):
        """Guardar dato en caché"""
        self.cache[key] = value
        self.tiempos[key] = datetime.now()
    
    def limpiar(self):
        """Limpiar caché expirado"""
        ahora = datetime.now()
        claves_a_eliminar = []
        for key, tiempo in self.tiempos.items():
            if (ahora - tiempo).seconds >= self.ttl:
                claves_a_eliminar.append(key)
        for key in claves_a_eliminar:
            del self.cache[key]
            del self.tiempos[key]

# Inicializar caché
cache_datos = CacheRapido(CACHE_TIEMPO_SEGUNDOS)

def get_datos_rapido(parcela_id):
    """Obtiene datos con caché para respuestas rápidas"""
    # Intentar obtener del caché
    datos_cached = cache_datos.get(parcela_id)
    if datos_cached:
        return datos_cached
    
    # Si no está en caché, consultar a MongoDB
    datos = recomendador.recomendar(parcela_id)
    cache_datos.set(parcela_id, datos)
    return datos

def get_todas_parcelas_rapido():
    """Obtiene datos de todas las parcelas con caché"""
    todas = {}
    for pid in PARCELAS.keys():
        todas[pid] = get_datos_rapido(pid)
    return todas

# =============================================================================
# FUNCIONES AUXILIARES
# =============================================================================

def extraer_datos_explicacion(explicacion):
    """Extrae datos estructurados de la explicación del recomendador"""
    datos = {
        'temp_aire': 'N/D',
        'humedad_amb': 'N/D',
        'viento': 'N/D',
        'et0': 'N/D',
        'proyeccion_estado': 'N/D',
        'proyeccion_tiempo': 'N/D',
        'rango_humedad': 'N/D',
        'variabilidad': 'N/D',
        'sensores_criticos': '✓ No hay sensores en estado crítico',
        'zona_seca': 'N/D',
        'temp_suelo_relacion': ''
    }
    
    # Extraer temperatura del aire
    match = re.search(r'Temperatura del aire:\s*([\d.]+)°C', explicacion)
    if match:
        datos['temp_aire'] = match.group(1)
    
    # Extraer humedad ambiental
    match = re.search(r'Humedad ambiental:\s*([\d.]+)%', explicacion)
    if match:
        datos['humedad_amb'] = match.group(1)
    
    # Extraer viento
    match = re.search(r'Velocidad del viento:\s*([\d.]+)\s*m/s', explicacion)
    if match:
        datos['viento'] = match.group(1)
    
    # Extraer ET0
    match = re.search(r'ET0\s*([\d.]+)\s*mm/día', explicacion)
    if match:
        datos['et0'] = match.group(1)
    
    # Extraer proyección
    match = re.search(r'PROYECCIÓN:\s*\n\s*•\s*Estado:\s*(.+?)(?:\n|$)', explicacion, re.IGNORECASE)
    if match:
        datos['proyeccion_estado'] = match.group(1).strip()
    
    match = re.search(r'Autonomía:\s*(.+?)(?:\n|$)', explicacion)
    if match:
        datos['proyeccion_tiempo'] = match.group(1).strip()
    
    # Extraer rango de humedad
    match = re.search(r'Rango de humedad:\s*([\d.]+%?\s*[-–]\s*[\d.]+%?)', explicacion)
    if match:
        datos['rango_humedad'] = match.group(1)
    
    # Extraer variabilidad
    match = re.search(r'Variabilidad de humedad:\s*([±\d.]+%?)', explicacion)
    if match:
        datos['variabilidad'] = match.group(1)
    
    # Extraer sensores críticos
    if 'SENSORES CRÍTICOS:' in explicacion:
        match = re.search(r'SENSORES CRÍTICOS:\s*(.+?)(?:\n|$)', explicacion)
        if match and 'ningún' not in match.group(1):
            datos['sensores_criticos'] = f"⚠ {match.group(1).strip()}"
    
    # Extraer zona más seca
    match = re.search(r'Zona más seca:\s*(.+?)(?:\n|$)', explicacion)
    if match:
        datos['zona_seca'] = match.group(1).strip()
    
    # Extraer relación temperatura suelo/aire
    match = re.search(r'🌡 Temperatura del suelo:\s*([\d.]+)°C\s*\((.+?)\)', explicacion)
    if match:
        datos['temp_suelo_relacion'] = f"🌡 Temperatura del suelo: {match.group(1)}°C ({match.group(2)})"
    
    return datos

def obtener_emoji_decision(decision):
    if decision == "No regar":
        return "✅"
    elif decision == "Regar pronto":
        return "⚠️"
    else:
        return "🔴"

def obtener_emoji_proyeccion(estado):
    if "crítico" in estado.lower():
        return "🔴"
    elif "moderado" in estado.lower() or "preventivo" in estado.lower():
        return "🟡"
    else:
        return "🟢"

def construir_reporte_texto(datos, datos_extra):
    """Construye el reporte de texto de forma rápida"""
    emoji_decision = obtener_emoji_decision(datos['decision'])
    emoji_proy = obtener_emoji_proyeccion(datos_extra['proyeccion_estado'])
    
    et0_val = float(datos_extra['et0']) if datos_extra['et0'] != 'N/D' else 0
    etc = et0_val * 0.85
    
    reporte = f"""
🌾 *REPORTE - {datos['nombre']}* 🌾
📅 {datetime.now().strftime('%H:%M:%S')}

🌤 *CLIMA:*
   🌡 {datos_extra['temp_aire']}°C | 💧 {datos_extra['humedad_amb']}%
   💨 {datos_extra['viento']} m/s | ☀️ ET0 {datos_extra['et0']} mm/día

{emoji_decision} *DECISIÓN:* {datos['decision']}
   💧 Humedad: {datos['theta']:.1%}

{emoji_proy} *PROYECCIÓN:* {datos_extra['proyeccion_estado']}

🖧 *SENSORES:* {datos['n_validos']}/12 operativos
   📊 {datos_extra['rango_humedad']}
   {datos_extra['temp_suelo_relacion'] if datos_extra['temp_suelo_relacion'] else ''}

✓ *Confianza:* {datos['confianza']:.0f}%
💦 *Riego:* {datos['lamina_mm']} mm | {datos['volumen_m3']} m³
    """
    return reporte

# =============================================================================
# FUNCIONES PARA GENERAR GRÁFICAS (OPTIMIZADAS)
# =============================================================================

def generar_grafica_barras(datos, parcela_id):
    """Versión optimizada y rápida de gráfica de barras"""
    fig, ax = plt.subplots(figsize=TAMANO_FIGURA)
    
    sensores = []
    humedades = []
    colores = []
    
    for sensor_id, s in datos['sensores'].items():
        if s['valido']:
            nombre = sensor_id.split('_')[-1]
            sensores.append(nombre)
            humedad = s['theta_sensor'] * 100
            humedades.append(humedad)
            
            if humedad >= SUELO['theta_umbral'] * 100:
                colores.append('#4CAF50')
            elif humedad >= SUELO['theta_critico'] * 100:
                colores.append('#FF9800')
            else:
                colores.append('#F44336')
    
    bars = ax.bar(sensores, humedades, color=colores, edgecolor='white', linewidth=0.5)
    
    ax.axhline(y=SUELO['theta_umbral'] * 100, color='#FF9800', linestyle='--', linewidth=1)
    ax.axhline(y=SUELO['theta_critico'] * 100, color='#F44336', linestyle='--', linewidth=1)
    
    ax.set_ylabel('Humedad (%)', fontsize=10)
    ax.set_title(f'{datos["nombre"]}', fontsize=12, fontweight='bold')
    ax.grid(True, alpha=0.2)
    
    for bar, hum in zip(bars, humedades):
        ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 1,
                f'{hum:.0f}%', ha='center', va='bottom', fontsize=8)
    
    plt.tight_layout()
    
    buf = io.BytesIO()
    plt.savefig(buf, format='png', dpi=DPI_GRAFICAS, bbox_inches='tight')
    buf.seek(0)
    plt.close()
    
    return buf

def generar_grafica_gauge(humedad):
    """Versión optimizada del velocímetro"""
    fig, ax = plt.subplots(figsize=(6, 5))
    
    porcentaje = humedad * 100
    
    if porcentaje >= SUELO['theta_umbral'] * 100:
        color = '#4CAF50'
        estado = "ÓPTIMO"
    elif porcentaje >= SUELO['theta_critico'] * 100:
        color = '#FF9800'
        estado = "ATENCIÓN"
    else:
        color = '#F44336'
        estado = "CRÍTICO"
    
    ax.pie([100], colors=['#333333'], startangle=90, counterclock=False)
    ax.pie([porcentaje, 100-porcentaje], colors=[color, '#333333'], 
           startangle=90, counterclock=False, wedgeprops={'width': 0.3})
    
    angle = (porcentaje / 100) * 180 - 90
    ax.annotate('', xy=(0.5*np.cos(np.radians(angle)), 0.5*np.sin(np.radians(angle))),
                xytext=(0, 0), arrowprops=dict(arrowstyle='->', color='white', lw=1.5))
    
    ax.text(0, 0, f'{porcentaje:.0f}%', ha='center', va='center', 
            fontsize=22, fontweight='bold', color=color)
    ax.text(0, -0.3, estado, ha='center', va='center', 
            fontsize=12, fontweight='bold', color=color)
    
    ax.axis('equal')
    plt.tight_layout()
    
    buf = io.BytesIO()
    plt.savefig(buf, format='png', dpi=DPI_GRAFICAS, bbox_inches='tight')
    buf.seek(0)
    plt.close()
    
    return buf

def generar_grafica_torta_sensores(sensores):
    """Versión optimizada de gráfica de torta"""
    estados = {'Óptimo': 0, 'Atención': 0, 'Crítico': 0, 'Offline': 0}
    
    for s in sensores.values():
        if not s['valido']:
            estados['Offline'] += 1
        elif s['theta_sensor'] >= SUELO['theta_umbral']:
            estados['Óptimo'] += 1
        elif s['theta_sensor'] >= SUELO['theta_critico']:
            estados['Atención'] += 1
        else:
            estados['Crítico'] += 1
    
    labels = [k for k, v in estados.items() if v > 0]
    values = [v for v in estados.values() if v > 0]
    colors = []
    
    for l in labels:
        if l == 'Óptimo':
            colors.append('#4CAF50')
        elif l == 'Atención':
            colors.append('#FF9800')
        elif l == 'Crítico':
            colors.append('#F44336')
        else:
            colors.append('#888888')
    
    fig, ax = plt.subplots(figsize=(6, 5))
    ax.pie(values, labels=labels, colors=colors, autopct='%1.0f%%', startangle=90, textprops={'fontsize': 10})
    ax.set_title('Estado Sensores', fontsize=12, fontweight='bold')
    
    buf = io.BytesIO()
    plt.savefig(buf, format='png', dpi=DPI_GRAFICAS, bbox_inches='tight')
    buf.seek(0)
    plt.close()
    
    return buf

def generar_grafica_ranking(todas_parcelas):
    """Versión optimizada del ranking"""
    fig, ax = plt.subplots(figsize=(8, 5))
    
    parcelas = []
    humedades = []
    colores = []
    
    for pid, datos in todas_parcelas.items():
        if datos:
            parcelas.append(f"{pid}")
            humedad = datos['theta'] * 100
            humedades.append(humedad)
            
            if humedad >= SUELO['theta_umbral'] * 100:
                colores.append('#4CAF50')
            elif humedad >= SUELO['theta_critico'] * 100:
                colores.append('#FF9800')
            else:
                colores.append('#F44336')
    
    orden = np.argsort(humedades)
    parcelas = [parcelas[i] for i in orden]
    humedades = [humedades[i] for i in orden]
    colores = [colores[i] for i in orden]
    
    bars = ax.barh(parcelas, humedades, color=colores, edgecolor='white', linewidth=0.5)
    
    ax.axvline(x=SUELO['theta_umbral'] * 100, color='#FF9800', linestyle='--', linewidth=1)
    ax.axvline(x=SUELO['theta_critico'] * 100, color='#F44336', linestyle='--', linewidth=1)
    
    ax.set_xlabel('Humedad (%)', fontsize=10)
    ax.set_title('Ranking de Parcelas', fontsize=12, fontweight='bold')
    ax.grid(True, alpha=0.2, axis='x')
    
    for bar, hum in zip(bars, humedades):
        ax.text(bar.get_width() + 1, bar.get_y() + bar.get_height()/2,
                f'{hum:.0f}%', va='center', fontsize=9)
    
    plt.tight_layout()
    
    buf = io.BytesIO()
    plt.savefig(buf, format='png', dpi=DPI_GRAFICAS, bbox_inches='tight')
    buf.seek(0)
    plt.close()
    
    return buf

# =============================================================================
# COMANDOS DE TELEGRAM (RÁPIDOS)
# =============================================================================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    welcome_msg = f"""
🌾 *SISTEMA IA DE RIEGO - SINALOA*

Hola {user.first_name}! Soy tu asistente de riego.

*Comandos rápidos:*
📊 `/reporte P01` - Reporte completo
🏆 `/ranking` - Ranking de parcelas
🔔 `/alertas` - Alertas activas
❓ `/ayuda` - Más comandos
"""
    await update.message.reply_text(welcome_msg, parse_mode='Markdown')

async def ayuda(update: Update, context: ContextTypes.DEFAULT_TYPE):
    help_msg = """
*📚 Comandos Rápidos*

*/reporte [parcela]* - Reporte ejecutivo
*/ranking* - Ranking de parcelas
*/alertas* - Alertas activas
*/grafica [parcela]* - Gráfica de sensores
*/gauge [parcela]* - Velocímetro
*/torta [parcela]* - Estado sensores

📌 *Parcelas:* P01, P02, P03, P04, P05
💡 *Ejemplo:* `/reporte P01`
    """
    await update.message.reply_text(help_msg, parse_mode='Markdown')

async def reporte_rapido(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Versión RÁPIDA del reporte - con caché"""
    args = context.args
    if not args:
        await update.message.reply_text("❌ Ej: `/reporte P01`", parse_mode='Markdown')
        return
    
    parcela_id = args[0].upper()
    if parcela_id not in PARCELAS:
        await update.message.reply_text(f"❌ Parcela '{parcela_id}' no existe")
        return
    
    inicio = time.time()
    
    # Usar caché para respuesta rápida
    datos = get_datos_rapido(parcela_id)
    datos_extra = extraer_datos_explicacion(datos['explicacion'])
    
    reporte = construir_reporte_texto(datos, datos_extra)
    
    await update.message.reply_text(reporte, parse_mode='Markdown')
    
    # Botón opcional para gráficas
    keyboard = [[InlineKeyboardButton("📊 Ver Gráfica", callback_data=f"graf_{parcela_id}")]]
    await update.message.reply_text(
        "¿Ver gráfica de sensores?",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )
    
    fin = time.time()
    print(f"⚡ Reporte generado en {fin-inicio:.2f} segundos")

async def ranking_rapido(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Ranking rápido con caché"""
    await update.message.reply_text("🏆 Generando ranking...")
    
    inicio = time.time()
    todas = get_todas_parcelas_rapido()
    buf = generar_grafica_ranking(todas)
    
    critica = min([d for d in todas.values() if d], key=lambda x: x['theta'])
    
    await update.message.reply_photo(
        photo=buf,
        caption=f"🏆 Ranking | Más crítica: {critica['nombre']} ({critica['theta']:.1%})"
    )
    
    fin = time.time()
    print(f"⚡ Ranking generado en {fin-inicio:.2f} segundos")

async def grafica_rapida(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Gráfica rápida de sensores"""
    args = context.args
    if not args:
        await update.message.reply_text("❌ Ej: `/grafica P01`", parse_mode='Markdown')
        return
    
    parcela_id = args[0].upper()
    if parcela_id not in PARCELAS:
        await update.message.reply_text(f"❌ Parcela '{parcela_id}' no existe")
        return
    
    await update.message.reply_text(f"📊 Generando gráfica...")
    
    inicio = time.time()
    datos = get_datos_rapido(parcela_id)
    buf = generar_grafica_barras(datos, parcela_id)
    
    await update.message.reply_photo(
        photo=buf,
        caption=f"📊 {datos['nombre']} | {datos['theta']:.1%} | {datos['decision']}"
    )
    
    fin = time.time()
    print(f"⚡ Gráfica generada en {fin-inicio:.2f} segundos")

async def gauge_rapido(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Gráfica rápida tipo gauge"""
    args = context.args
    if not args:
        await update.message.reply_text("❌ Ej: `/gauge P01`", parse_mode='Markdown')
        return
    
    parcela_id = args[0].upper()
    if parcela_id not in PARCELAS:
        await update.message.reply_text(f"❌ Parcela '{parcela_id}' no existe")
        return
    
    datos = get_datos_rapido(parcela_id)
    buf = generar_grafica_gauge(datos['theta'])
    
    await update.message.reply_photo(
        photo=buf,
        caption=f"🎯 {datos['nombre']} - {datos['decision']}\n💧 {datos['theta']:.1%}"
    )

async def torta_rapida(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Gráfica rápida de torta"""
    args = context.args
    if not args:
        await update.message.reply_text("❌ Ej: `/torta P01`", parse_mode='Markdown')
        return
    
    parcela_id = args[0].upper()
    if parcela_id not in PARCELAS:
        await update.message.reply_text(f"❌ Parcela '{parcela_id}' no existe")
        return
    
    datos = get_datos_rapido(parcela_id)
    buf = generar_grafica_torta_sensores(datos['sensores'])
    
    await update.message.reply_photo(
        photo=buf,
        caption=f"📡 {datos['nombre']} | {datos['n_validos']}/12 sensores OK"
    )

async def alertas_rapido(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Alertas rápidas"""
    todas = get_todas_parcelas_rapido()
    
    alertas_list = []
    for pid, datos in todas.items():
        if datos:
            if datos['theta'] < SUELO['theta_critico']:
                alertas_list.append(f"🔴 CRÍTICO - {datos['nombre']}: {datos['theta']:.1%}")
            elif datos['theta'] < SUELO['theta_umbral']:
                alertas_list.append(f"🟡 ATENCIÓN - {datos['nombre']}: {datos['theta']:.1%}")
    
    if alertas_list:
        mensaje = "🚨 *ALERTAS*\n\n" + "\n".join(alertas_list)
    else:
        mensaje = "✅ *Sin alertas* - Todo en orden"
    
    await update.message.reply_text(mensaje, parse_mode='Markdown')

async def callback_graficas(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Callback rápido para gráficas"""
    query = update.callback_query
    await query.answer()
    
    if query.data.startswith("graf_"):
        parcela_id = query.data.replace("graf_", "")
        await query.edit_message_text("📊 Generando...")
        
        datos = get_datos_rapido(parcela_id)
        buf = generar_grafica_barras(datos, parcela_id)
        
        await context.bot.send_photo(
            chat_id=update.effective_chat.id,
            photo=buf,
            caption=f"📊 {datos['nombre']} | {datos['theta']:.1%}"
        )

# =============================================================================
# MAIN
# =============================================================================

def main():
    application = Application.builder().token(TOKEN).build()
    
    # Comandos rápidos
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("ayuda", ayuda))
    application.add_handler(CommandHandler("reporte", reporte_rapido))
    application.add_handler(CommandHandler("ranking", ranking_rapido))
    application.add_handler(CommandHandler("grafica", grafica_rapida))
    application.add_handler(CommandHandler("gauge", gauge_rapido))
    application.add_handler(CommandHandler("torta", torta_rapida))
    application.add_handler(CommandHandler("alertas", alertas_rapido))
    
    # Callback
    application.add_handler(CallbackQueryHandler(callback_graficas))
    
    print("=" * 50)
    print("🤖 Bot RÁPIDO de Telegram iniciado...")
    print(f"⚡ Caché activado: {CACHE_TIEMPO_SEGUNDOS}s")
    print(f"📊 DPI gráficas: {DPI_GRAFICAS}")
    print("📋 Comandos: /reporte, /ranking, /grafica, /gauge, /torta, /alertas")
    print("=" * 50)
    
    application.run_polling()

if __name__ == "__main__":
    main()