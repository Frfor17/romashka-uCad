короче, надо запустить локально всё это? вот описание

python3 -m venv env
Set-ExecutionPolicy Unrestricted -Scope Process
env\Scripts\Activate


для запуска



uvicorn main:app --reload

для запуска бота

py tg_bot.py