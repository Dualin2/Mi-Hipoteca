import streamlit as st
from datetime import date
import calendar

st.set_page_config(page_title="Mi Hipoteca", page_icon="🏠", layout="wide")
st.title("🏠 Simulador de Amortización de Hipoteca")

def restar_meses(fecha, meses):
    mes = fecha.month - meses - 1
    año = fecha.year + (mes // 12)
    mes = (mes % 12) + 1
    dia = min(fecha.day, calendar.monthrange(año, mes)[1])
    return date(año, mes, dia)

def calcular_cuota(capital, interes_anual, meses):
    if interes_anual <= 0: return capital / meses
    i_m = (interes_anual / 100) / 12
    return (capital * i_m) / (1 - (1 + i_m)**(-meses))

st.sidebar.header("Datos de tu Hipoteca")
capital_inicial = st.sidebar.number_input("Capital Inicial (€)", min_value=0.0, value=150000.0, step=1000.0)
capital_pendiente = st.sidebar.number_input("Capital Pendiente actual (€)", min_value=0.0, value=88946.62, step=1000.0)
fecha_inicio = st.sidebar.date_input("Fecha de inicio", date(2009, 7, 28))
fecha_fin_teorica = st.sidebar.date_input("Fecha fin teórica", date(2044, 7, 28))
intereses_historicos = st.sidebar.number_input("Intereses históricos pagados (€)", value=39162.26, step=100.0)

capital_amortizado = capital_inicial - capital_pendiente
hoy = date.today()
meses_restantes = (fecha_fin_teorica.year - hoy.year) * 12 + (fecha_fin_teorica.month - hoy.month)
if hoy.day <= fecha_fin_teorica.day:
    meses_restantes += 1

st.sidebar.info(f"**Capital ya pagado:** {capital_amortizado:,.2f} €\n\n**Meses Restantes:** {meses_restantes}".replace(',', 'X').replace('.', ',').replace('X', '.'))

st.sidebar.subheader("Tipos de interés y Revisión")
euribor = st.sidebar.number_input("Euríbor actual (%)", min_value=-1.0, value=2.804, step=0.001, format="%.3f")
diferencial = st.sidebar.number_input("Tu diferencial (%)", min_value=0.0, value=1.000, step=0.001, format="%.3f")

st.sidebar.divider()
mes_revision_str = st.sidebar.selectbox("Mes de tu próxima revisión", ["Febrero", "Julio"])
mes_revision = 2 if mes_revision_str == "Febrero" else 7
euribor_proximo = st.sidebar.number_input("Próximo Euríbor previsto (%)", min_value=-1.0, value=2.804, step=0.001, format="%.3f")

st.sidebar.subheader("Simulación de Aportación Extra")
aportacion_extra = st.sidebar.number_input("Dinero extra al mes (€)", min_value=0.0, value=200.0, step=50.0)
aportacion_unica = st.sidebar.number_input("Aportación extra PUNTUAL HOY (€)", min_value=0.0, value=0.0, step=100.0, help="Para simular que metes un pellizco de golpe hoy (ej. para cuadrar Hacienda a fin de año).")

tipo_amortizacion = st.sidebar.radio(
    "Al amortizar, el banco bajará tu cuota. ¿Qué haces con ese ahorro?",
    ["Me lo guardo (Amortización Normal)", "Lo reinvierto (Bola de Nieve ⛄)"]
)

st.sidebar.subheader("🎯 Tu Objetivo de Libertad")
fecha_objetivo = st.sidebar.date_input("Quiero terminar de pagar en...", date(2036, 8, 28))

st.sidebar.subheader("Desgravación Fiscal")
desgrava = st.sidebar.checkbox("¿Desgravas por vivienda habitual?", value=True)
pagado_este_año = 0.0
if desgrava:
    pagado_este_año = st.sidebar.number_input("Pagado este año hasta hoy (€)", min_value=0.0, value=4482.07, step=100.0)

interes_anual = euribor + diferencial
interes_anual_proximo = euribor_proximo + diferencial

year_rev = hoy.year
if hoy.month > mes_revision or (hoy.month == mes_revision and hoy.day >= fecha_fin_teorica.day):
    year_rev += 1
fecha_rev = date(year_rev, mes_revision, fecha_fin_teorica.day)
meses_hasta_rev_bruto = (fecha_rev.year - hoy.year) * 12 + (fecha_rev.month - hoy.month)
if hoy.day <= fecha_fin_teorica.day:
    meses_hasta_rev_bruto += 1
meses_hasta_revision = meses_hasta_rev_bruto - 1 

if interes_anual > 0 and meses_restantes > 0 and capital_pendiente > 0:
    
    # --- 1. SIMULACIÓN BASE ---
    cap_base = capital_pendiente
    int_base_total = 0
    cuota_actual_banco = calcular_cuota(cap_base, interes_anual, meses_restantes)
    cuota_tras_revision_banco = cuota_actual_banco
    
    for m in range(1, meses_restantes + 1):
        if m == meses_hasta_revision + 1:
            cuota_tras_revision_banco = calcular_cuota(cap_base, interes_anual_proximo, meses_restantes - (m - 1))
            tasa = (interes_anual_proximo / 100) / 12
            c_mes = cuota_tras_revision_banco
        elif m > meses_hasta_revision:
            tasa = (interes_anual_proximo / 100) / 12
            c_mes = cuota_tras_revision_banco
        else:
            tasa = (interes_anual / 100) / 12
            c_mes = cuota_actual_banco
            
        i_mes = cap_base * tasa
        int_base_total += i_mes
        cap_base -= (c_mes - i_mes)
        
    intereses_totales_sin_amortizar = int_base_total
    
    st.header("Resumen Actual (Sin amortizar extra)")
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Cuota Actual", f"{cuota_actual_banco:.2f} €", f"Hasta {mes_revision_str}", delta_color="off")
    
    diff_cuota = cuota_tras_revision_banco - cuota_actual_banco
    color_diff = "inverse" if diff_cuota > 0 else "normal"
    col2.metric(f"Cuota tras Revisión ({interes_anual_proximo:.3f}%)", f"{cuota_tras_revision_banco:.2f} €", f"{diff_cuota:+.2f} €", delta_color=color_diff)
    
    col3.metric("Plazo Restante", f"{meses_restantes} meses")
    col4.metric("Fecha Fin", fecha_fin_teorica.strftime("%d/%m/%Y"))
    
    st.subheader("🩸 El dato doloroso (Intereses al Banco)")
    int_fut = f"{intereses_totales_sin_amortizar:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.')
    int_hist = f"{intereses_historicos:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.')
    int_glob = f"{(intereses_totales_sin_amortizar + intereses_historicos):,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.')
    
    col_p1, col_p2, col_p3 = st.columns(3)
    col_p1.metric("Ya regalados (Pasado)", f"{int_hist} €")
    col_p2.metric("Por regalar (Futuro)", f"{int_fut} €", "Calculado con tu revisión")
    col_p3.metric("Total Intereses Histórico", f"{int_glob} €", delta_color="inverse")
    
    st.divider()
    
    # --- 2. SIMULACIÓN CON APORTACIÓN EXTRA ---
    if aportacion_extra > 0 or aportacion_unica > 0:
        cap_sim = capital_pendiente - aportacion_unica
        int_sim_total = 0
        meses_simulados = 0
        
        while cap_sim > 0 and meses_simulados < meses_restantes:
            meses_simulados += 1
            
            if meses_simulados > meses_hasta_revision:
                int_anual_sim = interes_anual_proximo
                cuota_natural = cuota_tras_revision_banco
            else:
                int_anual_sim = interes_anual
                cuota_natural = cuota_actual_banco
                
            tasa = (int_anual_sim / 100) / 12
            i_mes = cap_sim * tasa
            int_sim_total += i_mes
            
            if tipo_amortizacion == "Lo reinvierto (Bola de Nieve ⛄)":
                pago_total = cuota_natural + aportacion_extra
            else:
                cuota_real_banco = calcular_cuota(cap_sim, int_anual_sim, meses_restantes - (meses_simulados - 1))
                pago_total = cuota_real_banco + aportacion_extra
                
            if pago_total > (cap_sim + i_mes):
                pago_total = cap_sim + i_mes
                
            cap_sim -= (pago_total - i_mes)
            
        meses_ahorrados = meses_restantes - meses_simulados
        intereses_ahorrados = intereses_totales_sin_amortizar - int_sim_total
        nueva_fecha_fin = restar_meses(fecha_fin_teorica, meses_ahorrados)
        int_ahorrados_fmt = f"{intereses_ahorrados:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.')
        
        texto_puntual = f" + {aportacion_unica:,.0f} € puntual".replace(',', '.') if aportacion_unica > 0 else ""
        if tipo_amortizacion == "Lo reinvierto (Bola de Nieve ⛄)":
            st.header(f"🚀 Efecto Bola de Nieve (Aportando {aportacion_extra} €/mes{texto_puntual}):")
            st.info("💡 Estás aplicando el **Método Bola de Nieve**: como el banco te va pidiendo menos cuota base cada mes, tú coges esa pequeña diferencia de ahorro y la reinviertes en la hipoteca. Tu esfuerzo de bolsillo nunca cambia, pero el capital que devoras crece espectacularmente.")
        else:
            st.header(f"🚶‍♂️ Amortización Normal (Aportando {aportacion_extra} €/mes{texto_puntual}):")
            st.info("💡 Estás aplicando la **Amortización Normal**: pagas al banco su cuota real (que irá bajando poco a poco) + tu extra limpio. El dinero que te ahorras en la cuota te lo guardas en tu bolsillo.")
            
        # --- CÁLCULO DE RENTABILIDAD (TIR) ---
        flujos = [0.0] * (meses_restantes + 1)
        flujos[1] -= aportacion_unica
        if desgrava:
            flujos[1] += (aportacion_unica * 0.15)
            
        for m in range(1, meses_simulados + 1):
            flujos[m] -= aportacion_extra
            if desgrava:
                flujos[m] += (aportacion_extra * 0.15) 
                
        for m in range(meses_simulados + 1, meses_restantes + 1):
            flujos[m] += cuota_actual_banco 
            
        low_r, high_r = 0.0, 0.1
        for _ in range(50):
            mid_r = (low_r + high_r) / 2
            npv = sum([flujos[i] / (1 + mid_r)**i for i in range(1, meses_restantes + 1)])
            if npv > 0: low_r = mid_r
            else: high_r = mid_r
        tir_anual = ((1 + low_r)**12 - 1) * 100
            
        col_a, col_b, col_c, col_d, col_e = st.columns(5)
        col_a.metric("Nuevo Plazo Restante", f"{meses_simulados} meses", f"-{meses_ahorrados} meses")
        col_b.metric("Nueva Fecha Fin", nueva_fecha_fin.strftime("%d/%m/%Y"))
        col_c.metric("Intereses Ahorrados", f"{int_ahorrados_fmt} €")
        col_d.metric("Años Ahorrados", f"{meses_ahorrados / 12:.1f} años")
        col_e.metric("Rentabilidad (TIR)", f"{tir_anual:.2f}%", "Limpio de impuestos")
            
        if desgrava:
            m_restantes_año = 12 - hoy.month
            if hoy.day <= fecha_fin_teorica.day: m_restantes_año += 1
            tot_proy = pagado_este_año + aportacion_unica
            for m in range(1, m_restantes_año + 1):
                if m > meses_hasta_revision:
                    c_n = cuota_tras_revision_banco
                else:
                    c_n = cuota_actual_banco
                tot_proy += (c_n + aportacion_extra)
                    
            tot_proy_fmt = f"{tot_proy:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.')
            
            st.divider()
            st.subheader("⚖️ Alerta de Desgravación Fiscal")
            if tot_proy > 9040:
                sob = tot_proy - 9040
                sob_fmt = f"{sob:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.')
                st.warning(f"CUIDADO: Pagarás aprox. **{tot_proy_fmt} €** este año. Estás perdiendo **{sob_fmt} €** de deducción.")
            else:
                st.info(f"Pagarás aprox. **{tot_proy_fmt} €** este año. Aún tienes margen hasta 9.040 €.")
                
    # --- 3. OBJETIVO DE LIBERTAD ---
    st.divider()
    st.header("🎯 Tu Plan de Ataque a Medida")
    m_obj = (fecha_objetivo.year - hoy.year) * 12 + (fecha_objetivo.month - hoy.month)
    if hoy.day <= fecha_objetivo.day: m_obj += 1
        
    if m_obj >= meses_restantes:
        st.info("Pon una fecha más agresiva para ver cuánto extra necesitas.")
    elif m_obj <= 0:
        st.error("¡Esa fecha ya ha pasado!")
    else:
        low = 0.0
        high = 10000.0
        optimo = 0
        for _ in range(50):
            mid = (low + high) / 2
            c_p = capital_pendiente - aportacion_unica
            m = 0
            while c_p > 0 and m < meses_restantes:
                m += 1
                if m > meses_hasta_revision:
                    c_nat = cuota_tras_revision_banco
                    int_a = interes_anual_proximo
                else:
                    c_nat = cuota_actual_banco
                    int_a = interes_anual
                
                t = (int_a / 100) / 12
                inter = c_p * t
                
                if tipo_amortizacion == "Lo reinvierto (Bola de Nieve ⛄)":
                    pago_tot = c_nat + mid
                else:
                    c_real = calcular_cuota(c_p, int_a, meses_restantes - (m - 1))
                    pago_tot = c_real + mid
                    
                if pago_tot > (c_p + inter): pago_tot = c_p + inter
                c_p -= (pago_tot - inter)
                
            if c_p <= 0 and m <= m_obj:
                high = mid
                optimo = mid
            else:
                low = mid
                
        esf_fmt = f"{optimo:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.')
        texto_puntual_obj = f" (habiendo aportado los {aportacion_unica:,.0f} € de golpe)".replace(',', '.') if aportacion_unica > 0 else ""
        st.info(f"Para conseguir liberarte el **{fecha_objetivo.strftime('%d/%m/%Y')}**{texto_puntual_obj}, necesitas sumar **{esf_fmt} € extra constantes** cada mes a tu cuota.")

else:
    st.warning("Valores inválidos.")
