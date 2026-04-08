
README EXECUÇÃO PRÁTICA — automatizador das faixas

1) Meter esta pasta em:
   C:\Users\JoseVitorinoQuintas\DoReal\17_mapeamento_base\09_orquestrador_api_faixas

2) Confirmar settings:
   00_config\settings_runtime.json

3) Definir a chave da API:
   set OPENAI_API_KEY=...     (na sessão atual do cmd)
   ou
   setx OPENAI_API_KEY "..."

4) Testar estado:
   python 08_scripts\cli.py --project-root C:\Users\JoseVitorinoQuintas\DoReal status

5) Ver a próxima peça sem chamar a API:
   python 08_scripts\cli.py --project-root C:\Users\JoseVitorinoQuintas\DoReal next
   python 08_scripts\cli.py --project-root C:\Users\JoseVitorinoQuintas\DoReal run-once --dry-run

6) Correr automático:
   python 08_scripts\cli.py --project-root C:\Users\JoseVitorinoQuintas\DoReal run-all --steps 20

Comportamento atual configurado:
- continua até max steps
- 1 ensaio por defeito
- publica logo na pasta canónica
- 3 tentativas por peça se o output vier mal
- abre a pasta no Windows Explorer depois de publicar o ficheiro

Diferença importante:
- criar pasta = criar a diretoria no disco
- abrir pasta = lançar a diretoria no Explorer para a veres automaticamente

O runtime lê diretamente:
C:\Users\JoseVitorinoQuintas\DoReal\16_validacao_integral\08_descida_expositiva_controlada

Não usa merges para funcionar.


CORREÇÃO .ENV
- esta versão já tenta ler automaticamente `OPENAI_API_KEY` a partir de `.env` na raiz do projeto (`project_root`)
- se não encontrar aí, sobe diretórios à procura de outro `.env`
- se a variável já estiver no ambiente, essa continua a prevalecer
