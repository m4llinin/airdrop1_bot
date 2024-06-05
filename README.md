## Для запуска требуются:

    Python >= 3.10
    PostgreSQL 16

## Настроить config

    В config/.env указать DATABASE_NAME DATABASE_USER DATABASE_PASS (название бд, имя пользователя и пароль для подключения)
    Для первоначального создания таблиц расскоментировать строки 11 и 12 в database/commands.py/__init__ и запустить бота.
    После не забыть их закоментировать обратно, иначе таблицы будут дропаться.

## Как сделать "claim airdrop"?
    В таблицу airdrops нужно сделать новый аирдроп, обязательно добавив дату старта, максимальное кол-во пользователей
    для получения аирдропа. Делается вручную напрямую в таблицу в бд. Формат ввода даты старта и окончания "ЧЧ:ММ ДД.ММ.ГГГГ".
    Если введена только дата старта, то аирдроп длится 1 минуту в указанную дату и время старта. Если обе даты указаны,
    то аирдроп длится в этот промежуток времени. После принятия участия в аирдропе id юзера добавляется в users_got, и он
    второй раз не может принять участие в этом же аирдропе.

## Как почистить бд?
    Либо повторить процедуру с расскомменитровать строк и стирается полностью база, либо вручную удалять строки юзера в
    таблице users и id из users_got в аирдропе.
    
