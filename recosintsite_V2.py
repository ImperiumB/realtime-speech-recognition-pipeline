##########Инициация запуска скрипта после после получения команды Originate в Астериск##########
log_it("-----====== Запускаем общение ======-----")
    
    CURRENT_STATE_VALUES.conversation_start_time = time.perf_counter()
    agi.set_variable("conversation_start_time", CURRENT_STATE_VALUES.conversation_start_time)
    
    log_it("-----====== Открываем канал связи ======-----")
    # Установить соединение с сервером.
    cred = grpc.ssl_channel_credentials()
    channel = grpc.secure_channel('stt.api.cloud.yandex.net:443', cred)
    stub = stt_service_pb2_grpc.RecognizerStub(channel)

    log_it("-----====== Авторизуемся в облаке ======-----")
    # Отправить данные для распознавания.
    it = stub.RecognizeStreaming(recognize_stt(), metadata=(
        ('authorization', f'Bearer {iam_token}'),
        ('x-folder-id', folder),
    ))

###################################Отправка данных################################################
# Прочитать аудиофайл и отправить его содержимое порциями.
    with os.fdopen(3, 'rb') as f:
        log_it("---=== STT Получили канал голоса линукса ===---")
        data = f.read(CHUNK_SIZE)
        log_it("---=== STT запускаем отправку данных ===---")
        while data != b'':
            if USE_EXTERNAL_EOU_CLASSIFIER and CURRENT_STATE_VALUES.eou_detected:
                log_it("___EOU___ Отправляем EOU = True")
                yield stt_pb2.StreamingRequest(chunk=stt_pb2.AudioChunk(data=data), eou={})
                CURRENT_STATE_VALUES.eou_detected = False
                CURRENT_STATE_VALUES.last_eou_time = datetime.now()
            else:
                yield stt_pb2.StreamingRequest(chunk=stt_pb2.AudioChunk(data=data))
            data = f.read(CHUNK_SIZE)

###################################Синтез текста в аудиофайл#######################################
def synthesize_tts(text, output_file) -> pydub.AudioSegment:
    log_it("---=== Запускаем TTS синтез текста в речь ===---")
    # Определить параметры запроса для синтеза речи.
    request = tts_pb2.UtteranceSynthesisRequest(
        text=text,
        output_audio_spec=tts_pb2.AudioFormatOptions(
            container_audio=tts_pb2.ContainerAudio(
                container_audio_type=tts_pb2.ContainerAudio.WAV
            )
        ),
        loudness_normalization_type=tts_pb2.UtteranceSynthesisRequest.LUFS,
        hints=[tts_pb2.Hints(voice=CURRENT_STATE_VALUES.Voice)]

#################################Создание файла и озвучивание в Астериске###########################
            my_file = Path(full_filename)
            if not my_file.is_file():
                log_it(f"Файл {full_filename} не существует - создаём")
                # Проверим наличие папки и создадим её, если нужно
                full_path = str(my_file.parent)
                if not os.path.exists(full_path):
                    log_it(f"play_text_to_speech: Создаём папку {full_filename}")
                    os.makedirs(full_path)
                # Синтезируем
                synthesize_tts(text, full_filename)

            # И наконец озвучим
            if do_it_async:
                log_it(f"Озвучиваем асинх: {text} | {filename}{CURRENT_STATE_VALUES.Voice}")
                agi.appexec("background", f"{audio_path}{filename}{CURRENT_STATE_VALUES.Voice}")
            else:
                log_it(f"Озвучиваем: {text} | {filename}{CURRENT_STATE_VALUES.Voice}")
                agi.appexec("background", f"{audio_path}{filename}{CURRENT_STATE_VALUES.Voice}")

#######################################Передача данных в ERP##########################################
log_it(f"CURL Обрабатываем текст: {recognizedText}")

        req_post = f'http://{CURRENT_STATE_VALUES.Aster2ServiceAddress}/ReturnConversationIntermediateResult3'
        # На стороне ERP это должно превратиться в Hashtable, поэтому и формат такой с Key+Value
        json_body = { 'prms': [
            { 'Key': 'conversationPoint'	, 'Value': CURRENT_STATE_VALUES.ConversationPoint },
            { 'Key': 'eventType'			, 'Value': event_type },
            { 'Key': 'conversationScenario'	, 'Value': CURRENT_STATE_VALUES.ConversationScenario },
            { 'Key': 'documentId'			, 'Value': CURRENT_STATE_VALUES.DocumentId },
            { 'Key': 'linkedId'				, 'Value': CURRENT_STATE_VALUES.LinkedId },
            { 'Key': 'recognizedText'		, 'Value': recognizedText },
            { 'Key': 'silenceDetected'		, 'Value': silence_detected },
            { 'Key': 'date_after_recognize'		, 'Value': str(CURRENT_STATE_VALUES.date_after_recognize) }
        ]}
        log_it(f'CURL JSON запрос к ERP:     {req_post}\n{json_body}')

        r = requests.post(req_post, timeout=15, json=json_body)
        status = r.status_code
        if status != 200:  # Если ответ не ОК, то прокинем ошибку. А вообще тут по-хорошему можно достать больше подробностей и отписать их в лог.
            log_it(f'Статус ответа на запрос:     {status}')
            r.raise_for_status()
            return None
          
###Проект разработан в соавторстве с glide1990@gmail.com
