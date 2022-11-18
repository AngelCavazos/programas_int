import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime
import streamlit as st
import re

def manipulacion(df):
    carreras = []
    for index in range(len(df)):
        valor = re.split('\d',df['Programa'].iloc[index])[0]
        valor = valor.strip()
        carreras.append(valor)
    df['Carrera']=carreras
    primera=[]
    for index in range(len(df)):
        substring = df['OportunidadesSeleccionadas'].iloc[index].partition('1 - ')[2]
        opcion = substring.split(',')[0]
        primera.append(opcion)
    df['1era Opcion'] = primera
    df['En 1era']= np.where(datos['1era Opcion']==datos['OportunidadAsignada'],1,0)
    return df

def p_int(df):
    for i in range(len(df)):
        value = df['OportunidadAsignada']
        x = re.findall("INT-", value)
        if len(x) == 1:
            return 'INT'
        else:
            return 'SA'

@st.cache
def data_load():
    df=pd.read_csv('Tablero_solicitudes_check.csv',delimiter=';')
    return df

    
#Visualización de página
st.set_page_config(page_title="Resultados de Análisis Internacional",layout='wide')
st.title("Analisis estudiantes al extranjero")
st.subheader("Realizado por Angel Cavazos A00827729")
st.header("Comparativa de tipos de planes internacionales")
sidebar = st.sidebar

#Por trabajarlo dentro de mi computadora tuve que poner el delimitador
#Carga de dataframes
df = data_load()
areas_carrera=pd.read_csv('Programas_Tec.csv',encoding='utf8')
regiones = pd.read_csv('Regiones_Campus.csv')
#df=pd.read_csv('Tablero_solicitudes_check.csv')

#Limpieza de datos
df = df.drop(['OportunidadesAprobadas','Actividad Actual'],axis=1)
#Tomamos solo aprobados
#asignados= df[df.Estatus == 'Asignada']
asignados= df[df.Estatus.isin(['Asignada','Asignado','Aprobada'])]

asignados['Ap Materno'].fillna('',inplace=True)
datos = asignados.copy()
datos = datos.dropna()
datos= datos[datos.Nivel != 'Indefinido']
#Manipulación de datos
datos = manipulacion(datos)

test = datos.merge(areas_carrera,how='left',left_on='Programa',right_on='Clave')
test= test.drop(['Area Academica','Clave','Programa Academico'],axis=1)
test = test.merge(regiones,'left','Campus')

test['P_Int']= test.apply(p_int,axis=1)

test['Fecha'] = pd.to_datetime(test['Fecha'])

#Construcción de dashboard

#Filtros 
regiones = test.Region.unique().tolist()
campus= test.Campus.unique().tolist()
escuela =test.Escuela.unique().tolist()
niveles = test.Nivel.unique().tolist()
test['Fecha'] = pd.to_datetime(test["Fecha"].dt.strftime('%Y-%m-%d'))

fecha_rango = st.slider('Fecha', 
            min_value= test['Fecha'].min().to_pydatetime(), 
            max_value = test.Fecha.max().to_pydatetime(),
            value = (test['Fecha'].min().to_pydatetime(),test.Fecha.max().to_pydatetime()))      

sidebar.header('Filtros de categoría')
region_select = sidebar.multiselect('Región',regiones,default=regiones)
# campus_select = st.multiselect('Campus', campus,default=campus)
escuela_select = sidebar.multiselect('Escuela',escuela,default=escuela)

nivel_select = sidebar.multiselect('Nivel',niveles,default='Profesional')

#Filtro basado en selección de usuario
mask = (test['Fecha'].between(*fecha_rango)) & (test['Region'].isin(region_select)) & (test['Escuela'].isin(escuela_select) & (test['Nivel'].isin(nivel_select)))
df = test[mask]
results = df.shape[0]
st.markdown(f'Resultados disponibles {results}')

#INT vs SA
#Desglose general
col1, col2 = st.columns(2)
count_int = df['Instancia'][df.P_Int == 'INT'].count()
count_sa = df['Instancia'][df.P_Int == 'SA'].count()
col1.markdown(F'Personas en intercambios: {count_int}')
col2.markdown(f'Personas en otro sistema: {count_sa}')

#Comparativa general INT vs SA
fig1 = px.pie(df, names='P_Int', title='Comparativa Intercambio - Study Abroad')
fig1.update_layout(width=500)

#Instancias por región
fig2 = px.histogram(df, x='Region',color='P_Int', title="Comparativa por región")
fig2.update_layout(width=500)

#Frecuencia de tipos de viajes respecto al tiempo
freq_INT = df[df.P_Int == 'INT'].groupby(df['Fecha'].astype('datetime64[M]'))['Instancia'].count().rename('Count').to_frame()
freq_SA = df[df.P_Int == 'SA'].groupby(df['Fecha'].astype('datetime64[M]'))['Instancia'].count().rename('Count').to_frame()
freq_INT['Tipo'] = 'INT'
freq_SA['Tipo'] = 'SA'
freq_tipo = pd.concat([freq_INT, freq_SA])

#Personas aprobadas a traves del tiempo y tipo de viaje
fig3 = px.line(freq_tipo,y='Count', title='Personas aprobadas a traves del tiempo',color='Tipo',markers=True,symbol='Tipo')
fig3.update_layout(width = 850)
col5, col6, col7 = st.columns([1,7,1])
col6.write(f'<p style =" text-align: center; font-size: 40px;"> Porcentaje de gente en intercambio</p>',unsafe_allow_html=True)
porcentaje = f'<p style="color:Red; font-size: 35px;text-align: center;"> <b>{round((count_int/count_sa)*100,2)} %</b></p>'
col6.markdown(porcentaje,unsafe_allow_html=True)
col6.write(fig3)

#Muestras por regiones
fig4 = px.treemap(df, path=[px.Constant("México"),'Region','Campus'],title='Aprobados por región y campus')
fig4.update_layout(width=550)

#Aprobados por carrera
fig5 = px.treemap(df, path=['Escuela','Carrera'], title='Aprobados por carrera')
fig5.update_layout(width=550)



col3, col4 = st.columns(2)
col3.write(fig2)
col4.write(fig1)
col3.write(fig4)
col4.write(fig5)

st.header("Analisis de personas en 1era oportunidad")
st.write(f'<p style =" text-align: center; font-size: 35px;"> Porcentaje de estudiantes en primer opción</p>',unsafe_allow_html=True)
primera = df['En 1era'].sum()
total = df['En 1era'].count()
st.markdown(f'<p style="color:Red; font-size: 30px;text-align: center;"> <b>{round((primera/total)*100,2)} %</b></p>',unsafe_allow_html=True)

#Grafica de porcentaje en primera opcion en base al tiempo
perc_enfecha= pd.DataFrame(df.groupby('Fecha')['En 1era'].sum())
perc_enfecha['Total']=df.groupby('Fecha')['En 1era'].count().values
perc_enfecha['%1era'] = round(perc_enfecha['En 1era']/perc_enfecha['Total'] *100,2)

fig6= px.line(perc_enfecha, y='%1era',range_y=[0,100],markers=True)
st.write(fig6)

#Porcentajes de primeras opción en campus
campus_perc = pd.DataFrame(df.groupby(['Region','Campus'])['En 1era'].sum())
campus_perc['Total']=df.groupby(['Region','Campus']).count()['En 1era'].values
campus_perc['Otra'] = campus_perc['Total'] - campus_perc['En 1era']
campus_perc['Porc'] = round((campus_perc['En 1era']/ campus_perc['Total'])*100,2)

campus_perc= campus_perc.reset_index()

fig7 = px.scatter(campus_perc, x="Porc", y="Total",
			size="En 1era", color="Region",hover_name="Campus",hover_data=['Otra'], size_max=70,range_x=[0,110],labels={'Total':'Instancias','Porc':'Porcentaje'})
fig7.update_layout(width=500,)
col8,col9 =st.columns(2)

col8.write(fig7)

#Porcentajes de primeras opción en Nivel
nivel_porc = pd.DataFrame(df.groupby('Nivel')['En 1era'].sum())
nivel_porc['Total']=df.groupby('Nivel').count()['En 1era'].values
nivel_porc['Otra'] = nivel_porc['Total'] - nivel_porc['En 1era']
nivel_porc['Porc'] = round((nivel_porc['En 1era']/ nivel_porc['Total'])*100,2)

fig9 = px.bar(nivel_porc,x=nivel_porc.index,y='Porc',color=nivel_porc.index,hover_data=['En 1era','Otra'],title='Porcentaje de personas en primera opción por nivel',labels={'Porc': 'Porcentaje'})

col9.write(fig9)

#Histograma de aceptados por promedio  en primera opción

fig10 = px.histogram(df,x='Promedio',color='P_Int',labels={'P_Int':'Plan de estudio'})

st.write(fig10)

#Promedio general por campus
df_query = pd.DataFrame(test.groupby(['Region','Campus'])['Promedio'].mean())

df_query= df_query.reset_index()
df_query.sort_values(['Region','Campus'])


fig11 = px.scatter(df_query, y=['Region','Campus'], x="Promedio", color="Region", symbol="Region",labels={'value':'Campus'})
fig11.update_yaxes(tickvals=df_query.Campus.unique())
fig11.update_layout(height= 1500,width =1200)
st.write(fig11)




