# Guion de exposición de la web

## 1. Inicio de la demostración

Buenos días/tardes. Voy a presentar la web del proyecto de Ética y Seguridad de Datos.

La aplicación está levantada con Docker. Esto significa que no estamos ejecutando cada parte manualmente, sino que todo corre en contenedores: PostgreSQL para la base de datos, FastAPI para el backend, React para el frontend y Nginx como punto de entrada.

La URL principal es:

```text
https://localhost:8443
```

Cuando entramos a esta URL, el navegador primero llega a Nginx. Nginx decide si debe enviar la solicitud al frontend o al backend. Por ejemplo, la página visual va al frontend, mientras que las rutas como `/api`, `/auth`, `/clientes` o `/campanias` van al backend FastAPI.

## 2. Página: Explorar el dataset

En esta primera pantalla vemos el resumen del dataset bancario.

Aquí el sistema está leyendo el archivo `bank.csv`, que corresponde al dataset Bank Marketing. El backend procesa este archivo y devuelve estadísticas generales al frontend.

En la parte superior se muestran datos como la cantidad de registros, la cantidad de columnas, los cuasi-identificadores y la distribución de la variable objetivo.

Los cuasi-identificadores son atributos que por sí solos quizás no identifican directamente a una persona, pero combinados pueden aumentar el riesgo de reidentificación. En este caso se usan campos como edad, trabajo, estado civil y educación.

También se muestran atributos sensibles, como balance, préstamos, vivienda o si el cliente contrató un depósito. Estos datos son relevantes porque pueden afectar la privacidad y el perfilamiento de los clientes.

En esta pantalla también aparece el análisis de k-anonimato. El k-anonimato nos ayuda a medir cuántas personas comparten una misma combinación de cuasi-identificadores. Si una combinación aparece solo una vez, el riesgo de reidentificación es mayor.

Entonces, esta página sirve como punto de partida: primero entendemos los datos y evaluamos qué tan sensibles pueden ser antes de aplicar técnicas de privacidad.

## 3. Página: Queries con privacidad diferencial

Ahora paso a la sección de queries con privacidad diferencial.

En esta pantalla se pueden ejecutar consultas agregadas sobre el dataset, por ejemplo promedios, conteos por categoría o histogramas.

La idea principal es comparar dos resultados: el valor real y el valor con privacidad diferencial. El valor real representa la consulta sin protección, mientras que el valor con privacidad diferencial incluye ruido controlado.

Aquí entra el concepto de epsilon. Epsilon controla el equilibrio entre privacidad y utilidad. Si epsilon es más pequeño, se agrega más ruido y la privacidad aumenta, pero el resultado puede ser menos exacto. Si epsilon es más grande, el resultado se parece más al valor real, pero la protección de privacidad es menor.

Este módulo permite visualizar ese intercambio. No se trata solo de obtener un resultado correcto, sino de evitar que una consulta agregada revele información sensible de personas individuales.

Por eso esta página demuestra cómo una organización puede consultar datos estadísticos sin exponer directamente a los clientes.

## 4. Página: Modelo con privacidad diferencial

Ahora paso a la página del modelo con privacidad diferencial.

En esta sección se compara un modelo base, entrenado sin privacidad diferencial, contra un modelo que aplica privacidad diferencial.

La pantalla muestra métricas como accuracy, F1 y ROC-AUC. Estas métricas sirven para evaluar qué tan bien funciona el modelo predictivo.

También se muestran métricas relacionadas con fairness, como diferencia de paridad demográfica y diferencia de oportunidad igualitaria. Esto es importante porque un sistema ético no solo debe proteger datos, sino también revisar si el modelo produce resultados desbalanceados entre grupos.

Lo que estamos mostrando aquí es el impacto de aplicar privacidad diferencial al aprendizaje automático. Al agregar privacidad, puede bajar un poco el rendimiento del modelo, pero se reduce el riesgo de que el modelo memorice o exponga información sensible del dataset.

Entonces, esta página resume una idea clave del proyecto: la privacidad tiene un costo, pero ese costo se puede medir y gestionar.

## 5. Página: Trade-off privacidad y utilidad

Ahora paso a la página de trade-off entre privacidad y utilidad.

Esta pantalla muestra cómo cambian las métricas del modelo cuando se modifica el valor de epsilon.

En la gráfica se puede observar que, con ciertos valores de epsilon, el modelo mantiene una utilidad aceptable. Pero si se exige demasiada privacidad, el ruido puede afectar más el desempeño.

La línea base representa el modelo sin privacidad diferencial. Esa línea sirve como referencia para comparar cuánto se pierde o se mantiene al aplicar protección.

Esta sección es importante porque en un proyecto real no basta con decir que se aplica privacidad diferencial. También hay que justificar qué nivel de privacidad se eligió y cómo afecta a los resultados.

Por eso esta página ayuda a tomar decisiones: permite encontrar un punto razonable entre proteger a las personas y mantener resultados útiles para el negocio.

## 6. Página: Resumen de proyecto

Ahora paso al resumen ético del proyecto.

Esta página conecta la parte técnica con los principios de ética y seguridad de datos.

Aquí se explica que el objetivo no es solamente construir una aplicación funcional, sino demostrar buenas prácticas en el tratamiento de datos personales.

Se consideran riesgos como la reidentificación, el uso indebido de información sensible, la falta de consentimiento y los posibles sesgos del modelo.

También se relaciona el proyecto con principios como minimización de datos, transparencia, control de acceso, trazabilidad y responsabilidad.

Esta sección funciona como una explicación conceptual: muestra por qué se eligieron controles como privacidad diferencial, gestión de consentimiento, roles, auditoría y cifrado.

## 7. Página: Usuarios del sistema

Ahora paso a la pantalla de usuarios del sistema.

Esta página muestra los usuarios demo que pueden utilizarse para probar el sistema. Cada usuario tiene un rol distinto.

Los roles permiten demostrar el control de acceso. Por ejemplo, un administrador tiene permisos más amplios, un supervisor puede gestionar campañas y asignaciones, un analista puede consultar información, y un teleoperador trabaja con sus contactos asignados.

Esto es importante porque en un sistema real no todos deben tener acceso a toda la información. El principio aplicado aquí es mínimo privilegio: cada usuario solo debe tener los permisos necesarios para cumplir su función.

Desde esta parte podemos copiar o revisar las credenciales demo y luego entrar al módulo bancario.

## 8. Página: Operación bancaria

Ahora entro al módulo de operación bancaria:

```text
https://localhost:8443/banca
```

Esta sección representa la parte operativa del sistema.

Primero aparece el login. El inicio de sesión se realiza contra el backend usando JWT. Cuando el usuario se autentica correctamente, el backend devuelve un token que incluye el rol y los permisos del usuario.

La interfaz cambia según esos permisos. Esto significa que no todos los usuarios ven las mismas opciones. El menú se arma dinámicamente según el rol autenticado.

## 9. Módulo bancario: Login

En esta pantalla ingreso con un usuario demo.

Al iniciar sesión, el sistema valida las credenciales en el backend. Si son correctas, se guarda la sesión y se muestra el panel correspondiente al rol.

Esto demuestra autenticación y control de acceso basado en roles.

Después del login, en la parte superior se puede ver el rol activo, la cantidad de permisos y que la sesión JWT está vigente.

## 10. Módulo bancario: Clientes

Ahora entro a la sección de clientes.

Aquí se muestran los clientes elegibles para campañas. Un punto importante es que no se muestran todos los clientes, sino aquellos que cumplen con la condición de consentimiento.

El sistema trabaja con consentimiento `opt-in`. Esto significa que el cliente autorizó el uso de sus datos para este tipo de operación.

En la tabla podemos ver información del cliente, su perfil, datos de contacto y si contrató o no el producto.

A la derecha está la gestión de consentimiento. Si selecciono un cliente, puedo revisar su estado de consentimiento y modificarlo según corresponda.

Este cambio queda registrado, porque la gestión de consentimiento es una acción sensible. Así se demuestra que el sistema no solo almacena datos, sino que respeta la autorización del titular.

## 11. Módulo bancario: Campañas

Ahora paso a la sección de campañas.

Aquí se pueden crear campañas bancarias y revisar las campañas existentes.

Una campaña tiene nombre, producto, fecha de inicio y estado. Puede estar planificada, activa, cerrada o cancelada.

Esta sección representa la parte de planificación comercial, pero con controles. No cualquier usuario puede crear o cerrar campañas; eso depende de los permisos del rol.

Por ejemplo, un supervisor o administrador puede crear campañas, mientras que otros roles solo podrían consultarlas.

Esto muestra cómo el sistema separa responsabilidades y evita que cualquier usuario realice acciones administrativas.

## 12. Módulo bancario: Asignaciones

Ahora paso a la sección de asignaciones.

Aquí se asigna un cliente a una campaña y a un teleoperador.

El sistema solo permite asignar clientes elegibles, es decir, clientes con consentimiento válido. También se selecciona una campaña activa o disponible y un teleoperador.

Esta parte es importante porque conecta el consentimiento con la operación real. No basta con tener campañas; el sistema debe impedir que se use un cliente que no dio autorización.

Cuando se crea una asignación, el teleoperador podrá verla en su propia vista de contactos.

## 13. Módulo bancario: Mis contactos

Ahora muestro la sección de mis contactos, que normalmente corresponde al rol teleoperador.

Aquí el usuario solo ve las asignaciones que le corresponden. No ve todas las campañas ni todos los clientes del sistema.

El teleoperador puede registrar el resultado de contacto, por ejemplo: contactado, no contesta, rechaza o interesado.

También puede agregar una observación.

Esta pantalla demuestra control de acceso a nivel operativo: cada usuario trabaja solo con la información necesaria para su tarea.

Además, los resultados registrados ayudan a cerrar el ciclo de la campaña y mantener trazabilidad.

## 14. Módulo bancario: Usuarios

Ahora paso a la sección de usuarios.

Esta sección está pensada para un administrador.

Aquí se pueden ver los usuarios registrados, sus roles y su estado activo o inactivo.

También se puede crear un usuario nuevo, asignarle un rol y una contraseña temporal.

La importancia de esta pantalla es que el acceso al sistema se administra desde roles. En lugar de dar permisos manualmente a cada persona, se asigna un rol y ese rol define qué puede hacer.

También se puede activar o desactivar usuarios. Esto es relevante cuando alguien deja de participar en el proceso o ya no debe tener acceso al sistema.

## 15. Módulo bancario: Auditoría

Ahora paso a la sección de auditoría.

Esta pantalla muestra eventos relevantes del sistema, como acciones realizadas, recurso afectado, resultado y fecha.

La auditoría es fundamental en seguridad porque permite reconstruir qué ocurrió dentro del sistema.

Por ejemplo, si alguien modifica un consentimiento, crea una campaña o registra una acción importante, el sistema puede dejar evidencia.

Esto ayuda a cumplir principios de trazabilidad, responsabilidad y control interno.

En un sistema que trata datos personales, no basta con controlar el acceso; también hay que registrar las acciones sensibles.

## 16. Cierre de la demostración

Para cerrar, esta web integra dos partes.

La primera parte es el dashboard de privacidad diferencial, donde analizamos el dataset, medimos riesgo de reidentificación, ejecutamos consultas protegidas y comparamos modelos con y sin privacidad diferencial.

La segunda parte es la operación bancaria, donde se aplican controles de seguridad como login con JWT, roles y permisos, gestión de consentimiento, asignaciones, usuarios y auditoría.

El objetivo del proyecto es demostrar que una solución de datos no debe enfocarse solo en funcionalidad. También debe considerar privacidad, seguridad, consentimiento, trazabilidad y uso ético de la información.

Con esto finalizo la explicación de la web.

## 17. Comandos útiles si preguntan cómo se levantó

Para levantar todo con Docker:

```bash
cd infra
docker compose up --build -d
```

Para cargar datos demo:

```bash
docker compose exec -T backend python -m app.seed.load_bank_csv
```

Para revisar servicios:

```bash
docker compose ps
```

URLs principales:

```text
https://localhost:8443
https://localhost:8443/banca
https://localhost:8443/health
```
