@echo off
echo Configuracion de Tareas Programadas para Trinity...

schtasks /create /tn "Trinity_Resumen" /tr "c:\Users\yerko\agentes\run_resumen.bat" /sc daily /st 07:00 /f
schtasks /create /tn "Trinity_Radar_Manana" /tr "c:\Users\yerko\agentes\run_radar.bat" /sc daily /st 07:30 /f
schtasks /create /tn "Trinity_Agenda" /tr "c:\Users\yerko\agentes\run_agenda.bat" /sc daily /st 08:00 /f
schtasks /create /tn "Trinity_Curiosidades_Manana" /tr "c:\Users\yerko\agentes\run_curiosidades.bat" /sc daily /st 08:30 /f

schtasks /create /tn "Trinity_Correo_Manana" /tr "c:\Users\yerko\agentes\run_correo.bat" /sc daily /st 09:00 /f
schtasks /create /tn "Trinity_Correo_Mediodia" /tr "c:\Users\yerko\agentes\run_correo.bat" /sc daily /st 12:00 /f
schtasks /create /tn "Trinity_Correo_Tarde" /tr "c:\Users\yerko\agentes\run_correo.bat" /sc daily /st 16:00 /f

schtasks /create /tn "Trinity_Radar_Tarde" /tr "c:\Users\yerko\agentes\run_radar.bat" /sc daily /st 18:00 /f
schtasks /create /tn "Trinity_Curiosidades_Tarde" /tr "c:\Users\yerko\agentes\run_curiosidades.bat" /sc daily /st 18:30 /f

echo === Tareas configuradas con exito ===
pause
