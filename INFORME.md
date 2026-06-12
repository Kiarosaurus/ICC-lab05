# Informe de Laboratorio 05 — Contenedores y Cloud

**Curso:** Computación Cognitiva / Arquitectura Cloud
**Aplicación:** Sistema de Gestión de Predicciones del Mundial de Fútbol
**Arquitectura:** 3 Capas (Presentación, Negocio, Datos) + Docker + AWS Academy

---

## Pregunta 1: Desarrollo de Aplicación en Capas (12 Puntos)

Se diseñó e implementó una aplicación web completa para la visualización de partidos del Mundial de Fútbol y el registro de predicciones de marcadores por parte de los usuarios. El desarrollo se ejecutó bajo una rigurosa arquitectura de tres capas independientes, asegurando que la capa de presentación no interactúe con el motor relacional y que la capa de acceso a datos desconozca por completo las reglas de negocio de la aplicación.

> **Nota de evolución:** en la Fase 1 (desarrollo local) la base de datos relacional fue **SQLite**; en la Pregunta 2 la capa de acceso a datos se migró a **PostgreSQL 15** sin modificar una sola línea de las capas de negocio ni de presentación, lo que evidencia la correcta separación de responsabilidades.

### 1.1. Arquitectura de Software y Árbol de Directorios

La separación física de responsabilidades quedó estructurada en WSL (Ubuntu) de la siguiente manera:

```text
s12lab/
├── app/
│   ├── main.py                       # Punto de entrada (lifespan, une las 3 capas)
│   ├── presentation/                 # CAPA 1: Presentación
│   │   ├── routes.py                 #   Rutas HTTP / controladores
│   │   ├── banderas.py               #   Filtro Jinja2 (país -> bandera emoji)
│   │   ├── templates/                #   Vistas HTML (base, partidos, predecir, predicciones)
│   │   └── static/styles.css         #   Estilos CSS propios (tema "Noche de Estadio")
│   ├── business/                     # CAPA 2: Lógica de Negocio
│   │   ├── partido_service.py        #   Sincronización idempotente desde la API
│   │   └── prediccion_service.py     #   Validaciones lógicas y semánticas de predicciones
│   └── data/                         # CAPA 3: Acceso a Datos
│       ├── database.py               #   Conexión a la BD, creación de tablas y reintentos de arranque
│       ├── partido_repository.py     #   SQL de partidos
│       ├── prediccion_repository.py  #   SQL de predicciones
│       ├── api_client.py             #   Consumidor HTTP de la API pública externa
│       └── mock_partidos.json        #   Dataset JSON de respaldo ante caídas de red
├── requirements.txt                  # Dependencias de la aplicación
└── INFORME.md
```

### 1.2. Diagrama de Bloques y Dependencias de la Arquitectura

El siguiente diagrama describe el flujo jerárquico unidireccional implementado en el sistema: cada capa solo conoce a la capa inmediatamente inferior.

```mermaid
flowchart TD
    U["🧑‍💻 Navegador Web (Cliente)"]

    subgraph CAPA1["CAPA DE PRESENTACIÓN — app/presentation/"]
        R["routes.py<br>(rutas HTTP / controladores)"]
        T["templates/ (Jinja2)<br>static/styles.css"]
    end

    subgraph CAPA2["CAPA DE LÓGICA DE NEGOCIO — app/business/"]
        PS["partido_service.py"]
        RS["prediccion_service.py<br>(validaciones estrictas)"]
    end

    subgraph CAPA3["CAPA DE ACCESO A DATOS — app/data/"]
        DBM["database.py"]
        PR["partido_repository.py"]
        PRE["prediccion_repository.py"]
        AC["api_client.py"]
    end

    BD[("Base de datos relacional<br>SQLite (Fase 1) → PostgreSQL 15 (Fase 2)")]
    API["☁️ API pública openfootball"]
    MOCK["mock_partidos.json<br>(respaldo local)"]

    U -->|"Peticiones HTTP (GET/POST)"| R
    R --> T
    R -->|"invoca servicios de negocio"| PS
    R -->|"invoca servicios de negocio"| RS
    PS --> AC
    PS --> PR
    RS --> PR
    RS --> PRE
    DBM -->|"DDL (crea tablas al iniciar)"| BD
    PR -->|"DML (SELECT / INSERT)"| BD
    PRE -->|"DML (SELECT / INSERT)"| BD
    AC -->|"HTTPS"| API
    AC -.->|"lectura local si falla la red"| MOCK
```

### 1.3. Diagrama de Entidad-Relación (Base de Datos)

El esquema relacional que soporta la integridad referencial del sistema se detalla a continuación:

```mermaid
erDiagram
    PARTIDOS ||--o{ PREDICCIONES : "recibe"
    PARTIDOS {
        int id PK
        int numero UK "Numero unico del encuentro"
        string ronda "Jornada / fase del torneo"
        string fecha "Fecha del encuentro"
        string equipo_local
        string equipo_visitante
        int goles_local "NULL si el partido no se ha disputado"
        int goles_visitante "NULL si el partido no se ha disputado"
    }
    PREDICCIONES {
        int id PK
        int partido_id FK "Integridad referencial hacia PARTIDOS"
        string usuario "Nombre de quien predice"
        string resultado "CHECK: local, empate o visitante"
        int goles_local "CHECK >= 0"
        int goles_visitante "CHECK >= 0"
        timestamp creado_en "DEFAULT now()"
    }
```

### 1.4. Flujo de Datos y Control de Excepciones Semánticas

Cuando un usuario registra una predicción, el sistema no inserta los datos a ciegas; primero recupera el partido correspondiente desde el repositorio y somete el marcador ingresado a una evaluación de coherencia lógica en la Capa de Negocio:

```mermaid
sequenceDiagram
    actor Usuario
    participant P as Presentación<br>routes.py
    participant N as Negocio<br>prediccion_service.py
    participant D as Datos<br>repositorios
    participant BD as Base de Datos

    Usuario->>P: POST /partidos/:id/predicciones (formulario)
    P->>N: registrar_prediccion(partido_id, usuario,<br>resultado, goles_local, goles_visitante)
    N->>D: buscar_por_id(partido_id)
    D->>BD: SELECT * FROM partidos WHERE id = %s
    BD-->>D: fila del partido
    D-->>N: partido
    N->>N: Validar usuario, rango de goles e invariante:<br>¿el marcador coincide con el resultado elegido?
    alt Los datos son lógicamente coherentes
        N->>D: guardar(predicción)
        D->>BD: INSERT INTO predicciones (...)
        N-->>P: éxito (id de la predicción)
        P-->>Usuario: HTTP 303 Redirect a /predicciones
    else El marcador contradice el resultado elegido
        N-->>P: ValueError (excepción semántica)
        P-->>Usuario: HTTP 400 con el formulario y la alerta de error
    end
```

### 1.5. Evidencias de Funcionamiento de la Pregunta 1 (Entorno Local)

#### Evidencia 1.5.1: Panel Principal de Navegación (Home)

Se implementó una interfaz responsiva con Bootstrap 5 bajo el concepto de diseño *"Noche de Estadio"*. Al iniciar, la aplicación consume de manera idempotente la API externa y almacena los **64 partidos** en la base de datos, renderizándolos en tarjetas dinámicas agrupadas por su respectiva jornada de competición, con el marcador real de cada encuentro.

![Home con los 64 partidos en tarjetas agrupadas por jornada](<screenshots/Fase 1 - Home.png>)

#### Evidencia 1.5.2: Apertura de Ticket de Encuentro para Predicción

Al pulsar el botón "Predecir" de un partido, la aplicación despliega la vista de registro de predicciones con la identidad visual de ambas selecciones (generada por el filtro Jinja2 `banderas.py`; en Windows los emoji de bandera se representan con el código ISO del país). En la captura se completa una predicción coherente: usuaria "Kiara", resultado "Gana Russia" y marcador 2-1.

![Formulario de predicción con datos válidos (2-1, Gana Russia)](<screenshots/Fase 1 - Subir Predicción Adecuada.png>)

#### Evidencia 1.5.3: Ingreso de una Predicción Lógicamente Incoherente

La robustez de la Capa de Negocio se demuestra ingresando datos incoherentes: se digitó un marcador de **0 goles para Rusia y 2 para Arabia Saudita** (victoria visitante), pero se mantuvo seleccionada deliberadamente la opción **"Gana Russia"**.

![Formulario con marcador 0-2 pero resultado "Gana Russia"](<screenshots/Fase 1 - Predicción Inadecuada.png>)

#### Evidencia 1.5.4: Renderizado de Mensajes de Error Semánticos (HTTP 400)

Al procesar el POST incoherente del paso anterior, la capa de presentación captura el `ValueError` devuelto por la Lógica de Negocio y vuelve a renderizar el formulario con una alerta contextual que detalla el fallo: *"El marcador 0-2 implica victoria de Saudi Arabia, pero elegiste victoria de Russia. Corrige la predicción."*

![Alerta de error semántico devuelta por el servidor (HTTP 400)](<screenshots/Fase 1 - Predicción Inadecuada Mensaje Error.png>)

#### Evidencia 1.5.5: Persistencia Relacional y Consulta de Predicciones

Las predicciones que superan los criterios de integridad se insertan asociadas a su partido (clave foránea `partido_id`) y el usuario es redirigido a la vista consolidada. Se observa la predicción registrada en 1.5.2 (Kiara, Russia, 2-1) con su fecha de registro en UTC.

![Vista "Mis Predicciones" con el registro persistido](<screenshots/Fase 1 - Página predicciones.png>)

---

## Pregunta 2: Dockerización y Despliegue Cloud (8 Puntos)

Para aislar la aplicación de configuraciones de hardware locales y garantizar su portabilidad en entornos de producción, se encapsuló la solución bajo una arquitectura multi-contenedor.

### 2.1. Arquitectura de Contenedores Local (Dockerfile + `docker-compose.yml`)

Se reemplazó la base de datos SQLite de la fase de desarrollo por un motor **PostgreSQL 15**, y se construyó un **`Dockerfile`** optimizado para la aplicación: imagen base ligera `python:3.12-slim`, instalación de dependencias antes de copiar el código (aprovechando la caché de capas) y ejecución con un usuario sin privilegios de root. El entorno orquestado define dos servicios:

* `web`: backend FastAPI construido desde el `Dockerfile`, exponiendo el puerto interno 8000 hacia el puerto 8000 del host.
* `db`: imagen oficial `postgres:15` con almacenamiento persistente mediante el volumen nombrado de Docker **`datos_postgres`**, lo que impide la pérdida de información ante la destrucción y recreación del contenedor. Incluye un `healthcheck` (`pg_isready`) que obliga al contenedor `web` a esperar (`depends_on: condition: service_healthy`) a que PostgreSQL acepte conexiones.

La configuración sensible viaja por **variables de entorno** definidas en `.env` y `docker-compose.yml`: `POSTGRES_USER`, `POSTGRES_PASSWORD` y `POSTGRES_DB` para el servicio `db`, y `DB_HOST`, `DB_PORT`, `DB_NAME`, `DB_USER`, `DB_PASSWORD` para el servicio `web` (leídas por `database.py`). Como defensa adicional, `database.py` implementa un mecanismo de reintentos (`esperar_base_de_datos()`) por si la aplicación arrancara antes que la base de datos.

#### Evidencia 2.1.1: Estado de Salud de la Infraestructura de Contenedores

Mediante `docker ps` se comprueba el correcto aislamiento de los contenedores locales: `mundial-db` (postgres:15) se reporta en estado saludable (`healthy`) y `mundial-web` publica el puerto 8000, tras haberse inicializado correctamente contra la base de datos.

![docker ps con mundial-web (puerto 8000) y mundial-db healthy](<screenshots/Fase 2 - Docker ps.png>)

#### Evidencia 2.1.2: Validación del Funcionamiento Multi-Contenedor

Captura del navegador accediendo a la aplicación dockerizada local en `http://localhost:8000`. Esto comprueba que los repositorios de la capa de datos migraron exitosamente del dialecto SQLite al de PostgreSQL (placeholders `%s`, `ON CONFLICT ... DO NOTHING`, `RETURNING id`), manteniendo el frontend totalmente transparente para el cliente.

![Aplicación dockerizada sirviendo los 64 partidos desde PostgreSQL](<screenshots/Fase 2 - App corriendo correctamente.png>)

---

### 2.2. Publicación de la Solución en Docker Hub

Para que cualquier proveedor de computación en la nube pueda descargar el artefacto de software de forma inmutable, la imagen local se etiquetó y publicó en el registro público de Docker Hub bajo el repositorio `kiarosaurus/mundial-web:latest`:

```bash
docker tag s12lab-web:latest kiarosaurus/mundial-web:latest
docker push kiarosaurus/mundial-web:latest
```

#### Evidencia 2.2.1: Repositorio en Docker Hub (Vista de Perfil)

Se visualiza la cuenta `kiarosaurus` en Docker Hub confirmando la creación del repositorio `kiarosaurus/mundial-web` dedicado a la imagen del laboratorio.

![Perfil de Docker Hub con el repositorio mundial-web recién publicado](<screenshots/Fase 3 - Image en Profile.png>)

#### Evidencia 2.2.2: Tag y Digest de la Imagen Publicada

Vista detallada del repositorio público donde se certifica la publicación con la etiqueta `latest`, digest `sha256:1e4cf037a...` y un tamaño comprimido de 58.1 MB (gracias a la imagen base slim), lista para su distribución global vía `docker pull`.

![Detalle del repositorio: tag latest, digest sha256 y tamaño](<screenshots/Fase 3 - Image.png>)

---

### 2.3. Despliegue e Infraestructura Automatizada en AWS Cloud

Tomando en cuenta las restricciones administrativas del entorno educativo **AWS Academy** (no se permite crear roles IAM personalizados, políticas ni VPCs nuevas), el aprovisionamiento se automatizó al 100% mediante scripts que consumen la **AWS CLI**, apoyándose exclusivamente en la infraestructura por defecto de la cuenta:

1. `deploy_aws.sh`: descubre automáticamente la **VPC por defecto** y una de sus subredes públicas; crea el **Security Group** `mundial-sg` con reglas de firewall para tráfico TCP entrante en los puertos `80` (HTTP), `8000` (app) y `22` (SSH); resuelve la última AMI oficial estable de **Ubuntu 24.04** consultando el parámetro público de Canonical en SSM; y lanza una instancia **EC2 `t3.micro`** en esa subred con IP pública, el key pair `vockey` del laboratorio, la etiqueta `Name=mundial-web` y el `user_data.sh` inyectado. Finalmente espera a que la instancia esté `running` y reporta su IP pública.
2. `user_data.sh`: script ejecutado en el primer arranque de la EC2 (cloud-init) que automatiza el aprovisionamiento interno: instala de forma desatendida Docker y el plugin de Compose, escribe un `docker-compose.yml` **de producción** —que en lugar de hacer build descarga la imagen `kiarosaurus/mundial-web:latest` desde Docker Hub y levanta también `postgres:15` con su volumen persistente— y ejecuta `docker compose up -d`, publicando la aplicación en los puertos 80 y 8000.

#### Evidencia 2.3.1: Instancia Aprovisionada en la Consola AWS

Captura del panel de AWS EC2 que muestra la instancia `mundial-web` (`i-0a173ac8227f37622`) creada automáticamente por el script, junto con su resumen de detalles (IP pública e IP privada asignadas dentro de la VPC por defecto).

![Consola EC2 con la instancia mundial-web aprovisionada](<screenshots/Fase 3 - Running Instances 1.png>)

#### Evidencia 2.3.2: Instancia EC2 Activa en Producción

Confirmación desde la consola: la instancia se encuentra en estado **Running**, asociada al security group `mundial-sg` y al key pair `vockey`, exponiendo la dirección IP pública productiva **`107.20.57.56`**.

![Detalle de la instancia: estado Running, mundial-sg, vockey e IP pública](<screenshots/Fase 3 - Running Instances 2.png>)

---

### 2.4. Pruebas End-to-End (E2E) y Validaciones en la Nube

Una vez aprovisionado el entorno en AWS, se testeó la aplicación real expuesta en internet a través de la IP pública `107.20.57.56`. Las validaciones operan en **defensa en profundidad**: el formulario HTML limita los valores en el navegador (`min=0`, `max=20`), la Capa de Negocio re-valida el rango 0–20 y la coherencia semántica en el servidor, y la base de datos impone sus propios `CHECK`.

#### Evidencia 2.4.1: Registro de una Predicción Válida en Producción

Acceso al formulario productivo servido desde AWS. La interfaz se renderiza de forma fluida y se completa una predicción coherente del usuario "DemoCloud": victoria de Rusia 3-0.

![Formulario en producción (107.20.57.56) con predicción válida 3-0](<screenshots/Fase 3 - Predecir.png>)

#### Evidencia 2.4.2: Validación de Límite Superior de Goles

Se intentó ingresar un marcador absurdo de **50 goles**. La primera línea de defensa (atributo `max="20"` del formulario) bloquea el envío en el propio navegador con el mensaje *"El valor debe ser inferior o igual a 20"*; la misma regla existe en la Capa de Negocio (rango máximo de 20 goles), que la haría cumplir ante cualquier petición construida fuera del formulario.

![Bloqueo del valor 50 por el límite superior del formulario](<screenshots/Fase 3 - Error max 20.png>)

#### Evidencia 2.4.3: Validación de Límite Inferior (Valores Negativos)

Análogamente, al intentar registrar **-1 goles** el formulario lo rechaza con *"El valor debe ser superior o igual a 0"*. Esta regla también está replicada en la Capa de Negocio y como restricción `CHECK (goles >= 0)` en las columnas de PostgreSQL, garantizando la consistencia matemática de las tablas incluso ante clientes manipulados.

![Bloqueo del valor -1 por el límite inferior del formulario](<screenshots/Fase 3 - Error min 0.png>)

#### Evidencia 2.4.4: Control de Incoherencia Lógica en Producción

Prueba de la validación semántica del servidor en la nube: se envió un marcador de **2-1** (victoria local) seleccionando la opción **"Empate"**.

![Envío de la predicción incoherente: marcador 2-1 con resultado Empate](<screenshots/Fase 3 - Predicción Incoherente.png>)

El backend en AWS rechaza la transacción con HTTP 400 y devuelve el formulario con el detalle exacto de la contradicción: *"El marcador 2-1 implica victoria de Russia, pero elegiste un empate. Corrige la predicción."* El dato corrupto nunca llega a la base de datos.

![Respuesta del servidor: alerta de incoherencia y registro bloqueado](<screenshots/Fase 3 - Error Incoherencia.png>)

#### Evidencia 2.4.5: Persistencia y Escritura Exitosa en PostgreSQL Cloud

Las predicciones válidas del usuario "DemoCloud" (3-0 y 2-1, ambas victoria de Rusia) superaron todos los filtros y quedaron almacenadas en el volumen persistente del contenedor PostgreSQL en AWS, listadas con su marca de tiempo UTC. Esto demuestra el funcionamiento integral de la arquitectura de software y de su despliegue automatizado en la nube.

![Vista "Mis Predicciones" en producción con los registros persistidos](<screenshots/Fase 3 - Mis Predicciones.png>)