import numpy as np
import matplotlib.pyplot as plt
from scipy.io import wavfile
from scipy.signal import correlate, find_peaks, butter, lfilter
from scipy.integrate import simpson
import sounddevice as sd
from mls import mls
import flet as ft

# Configurações
fs = 8000
Ts = 1 / 10  # Mesmos parâmetros que TX

def grava(tempo, fs):

    # Modo escuta
    xrec = sd.rec(int(tempo*fs), samplerate=fs, channels=1, dtype='float64')
    sd.wait()

    # Salva o arquivo de áudio
    wavfile.write('audiorecorded.wav', fs, (xrec.flatten() * 32767).astype(np.int16))
    return(xrec)

def extrai(xrec, f0, f1, larg, alt):

    # Sincronização da mensagem
    seq = (np.round(mls(4, 1)) + 1) / 2
    t = np.arange(0, Ts, 1/fs)

    s0 = np.cos(2 * np.pi * t * f0)
    s1 = np.cos(2 * np.pi * t * f1)

    # Modulamos nossa sequência de sinalização
    seq_m = np.concatenate([s1 if val == 1 else s0 for val in seq])

    #filtros passa-banda
    nyquist = 0.5 * fs
    low1 = 0.9 * f0 / nyquist
    high1 = 1.1 * f0 / nyquist
    b, a = butter(4, [low1, high1], btype='band')

    low2 = 0.9 * f1 / nyquist
    high2 = 1.1 * f1 / nyquist
    d, c = butter(4, [low2, high2], btype='band')

    #sinal filtrado
    fxrec = lfilter(b, a, xrec) + lfilter(d, c, xrec)

    #normaliza o audio
    fxrec = fxrec / np.max(np.abs(fxrec))

    # Correlaciona
    xc = correlate(fxrec.flatten(), seq_m)
    xca = xc ** 2

    # Procuramos o início e fim da mensagem
    peaks, props = find_peaks(xc, distance=fs*Ts+50, height=0.25 * np.max(xc))
    peak_heights = props['peak_heights']
    picos_ind = np.argsort(peak_heights)[::-1]

    if len(peaks) >= 2:

        in1 = peaks[picos_ind[0]]
        in2 = peaks[picos_ind[1]]

        # Extraindo a mensagem com correção nos limites
        deslocamento = len(seq_m) - 1
        start_idx = max(in1 + 1, 0)  # Garantimos que o índice não seja negativo
        end_idx = min(in2 - deslocamento, len(fxrec)) # Garantimos que não exceda o tamanho de xrec
        aux = round((end_idx - start_idx)/(fs*Ts))
        end_idx = int(aux * fs * Ts + start_idx)

        s2 = fxrec[start_idx:end_idx].flatten()  # Extraindo a parte do sinal

        plt.figure(figsize=(larg,alt))
        plt.subplot(3, 1, 1)
        plt.plot(fxrec)
        plt.axis([0, len(fxrec), -1.2*max(fxrec), 1.2*max(fxrec)])
        plt.title('Áudio Original')

        plt.subplot(3, 1, 2)
        plt.plot(np.arange(len(xca)), xca)
        plt.xlim([0, len(xca)])
        plt.title('Correlação Cruzada')

        tv = np.arange(len(s2))

        plt.subplot(3, 1, 3)
        plt.plot(tv + start_idx, s2)
        plt.axis([0, len(fxrec), -1.2*max(fxrec), 1.2*max(fxrec)])
        plt.title('Resultado (Só a Mensagem)')

        plt.tight_layout()
        plt.savefig("graf2.svg")
        return(s0,s1,s2)
    
    else:
        return("error")

def traduz(s0,s1,s2):
    # Detecção Coerente

    seg_len = fs*Ts
    if len(s2) >= seg_len:
        print(len(s2))
        t1 = np.array_split(s2, round(len(s2) / seg_len))
        res = []
        for segment in t1:
            if len(segment) == seg_len:
                x1 = abs(simpson(segment * s1))
                x0 = abs(simpson(segment * s0))
                res.append(1 if x1 > x0 else 0)

        # Decodificação (Bits para Texto)
        mr = []
        for i in range(0, len(res), 7):
            if i + 6 < len(res):
                de = int(''.join(map(str, res[i:i+7])), 2)
                mr.append(chr(de))
        return(mr)
    else:
        return(['E','r','r','o'])

def main(page: ft.Page):

    def gravando(e):

        if tempo.content.value != "":
            
            page.controls.clear()
            page.add(status,parar)
            e.control.data = grava(int(tempo.content.value),fs)
            page.controls.clear()
            page.add(topo,player,freqs,extrair,audio)

    def parando(e):

        sd.stop()

    def extraindo(e):

        e.control.data = extrai(gravar.content.data, freqs.controls[0].controls[2].value, freqs.controls[1].controls[2].value,page.width/80, page.height/120)
        if e.control.data != "error":
            grafcon.content = ft.Image(
                src = "graf2.svg",
            )
            page.add(grafcon, decodificar)
        else:
            if decodificar in page.controls:
                if msg in page.controls:
                    page.remove(grafcon,decodificar,msg)
                else:    
                    page.remove(grafcon,decodificar)
            page.add(msg_error)

    def f0_change(e):

        t0.value = f"{e.control.value:.0f}"
        page.update()

    def f1_change(e):

        t1.value = f"{e.control.value:.0f}"
        page.update()

    def decodificando(e):

        msg.content.value = ''.join(traduz(extrair.content.data[0], extrair.content.data[1], extrair.content.data[2]))
        if msg in page.controls:
            msg.update()
        else:
            page.add(msg)

    page.window.maximized = True
    page.title = "Recepção BFSK"

    status = ft.Container(
        ft.Text(
            "Gravando...",
        ),
        alignment=ft.alignment.center,
    )

    tempo = ft.Container(
        ft.TextField(
            hint_text= "Por quanto tempo gravar o áudio? (s)",
        ),
        expand=True
    )

    gravar = ft.Container(
        ft.ElevatedButton(
            text = "Gravar",
            on_click = gravando,
        ),
    )

    topo = ft.Row(
        [tempo,gravar],
        alignment = ft.alignment.top_center,
    )

    parar = ft.Container(
        ft.ElevatedButton(
            text = "Parar",
            on_click = parando,
        ),
        alignment = ft.alignment.center,
        expand = True,
    )

    t0 = ft.Text("0") # texto que representa a frequência atual de f0
    t1 = ft.Text("0") # texto que representa a frequência atual de f1

    # Coluna de elementos contendo duas fileiras de textos das frequências f0 e f1 e seus respectivos sliders
    freqs = ft.Column(
        [
            ft.Row(
                [
                    ft.Text("f0 (Hz):"),
                    t0,
                    ft.Slider(
                        min=0,
                        max=1000,
                        divisions=100,
                        label="{value}",
                        on_change_end=f0_change,
                        expand = True
                    ),
                ],
                expand=True,
                alignment=ft.alignment.center,
            ),
            ft.Row(
                [
                    ft.Text("f1 (Hz):"),
                    t1,
                    ft.Slider(
                        min=0,
                        max=1000,
                        divisions=100,
                        label="{value}",
                        on_change_end=f1_change,
                        expand = True
                        ),
                ],
                expand=True,
                alignment=ft.alignment.center,
            ),
        ],
    )

    extrair = ft.Container(
        ft.ElevatedButton(
            text = "Extrair",
            on_click = extraindo,
        ),
        alignment = ft.alignment.center,
    )

    grafcon = ft.Container(
        alignment=ft.alignment.center,
    )

    decodificar = ft.Container(
        ft.ElevatedButton(
            text = "Decodificar",
            on_click = decodificando,
        ),
        alignment = ft.alignment.center,
    )

    msg = ft.Container(
        ft.Text(
            value = "",
            size = 20,
            expand = True,
        ),
        alignment = ft.alignment.center,
        expand = True,
    )

    msg_error = ft.Text("Mensagem não pode ser extraida")

    audio = ft.Audio(src="audiorecorded.wav", autoplay = False) # elemento de áudio da interface que tem o arquivo .wav como fonte

    play = ft.ElevatedButton("Play", on_click=lambda _: audio.resume()) # botão que toca o áudio do começo

    pause = ft.ElevatedButton("Pause", on_click=lambda _: audio.pause()) # botão que pausa o áudio

    replay = ft.ElevatedButton("Replay", on_click=lambda _: audio.play()) # botão que continua o áudio depois de pausar ou toca do começo caso não tenha sido reproduzido ainda

    player = ft.Row(
        [
            ft.Container(
                play,
            ),
            ft.Container(
                pause,
            ),
            ft.Container(
                replay,
            )
        ],
        alignment=ft.MainAxisAlignment.CENTER,
    )

    page.add(topo)

ft.app(target=main)