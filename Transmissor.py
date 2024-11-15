import numpy as np
import matplotlib.pyplot as plt
from scipy.io.wavfile import write
from mls import mls
import flet as ft

def de2bi(value, num_bits):
    return np.array(list(np.binary_repr(value, width=num_bits)), dtype=int) #Converte um número decimal em um número binário

def transmitir(mensagem,larg,alt,f0,f1):

    # Codificação e Sinalização
    bts = np.array([de2bi(ord(char), 7) for char in mensagem]).flatten()
    seq = (np.round(mls(4, 1)) + 1) / 2  # Max sequência de correlação

    bts = np.concatenate([seq, bts, seq])  # Info. [Início TEXT END]

    fs = 8000  # Amostragem
    Ts = 1 / 10  # Período de símbolo
    t = np.arange(0, Ts, 1 / fs)

    s0 = 2 * np.cos(2 * np.pi * f0 * t)  # Sinal cos[t] para f0
    s1 = 2 * np.cos(2 * np.pi * f1 * t)  # Sinal cos[t] para f1

    # Modulação (BFSK)
    sr = []

    for bit in bts:
        if bit == 1:
            sr.extend(s1)
        else:
            sr.extend(s0)

    sr = np.array(sr)

    # Gráficos
    plt.figure(figsize=(larg, alt))

    plt.subplot(2, 1, 1)
    plt.plot(np.repeat(bts[7:14], len(s0)), "r")
    plt.axis([0, 5607, -0.1, 1.1])
    plt.title('Bits to transmit')

    plt.subplot(2, 1, 2)
    plt.plot(sr[7 * len(s0): 2 * 7 * len(s0)], "b")
    plt.axis([0, 5607, -2.5, 2.5])
    plt.title('Modulated bits')

    plt.tight_layout()
    plt.savefig("graf.svg")

    # Arquivo de áudio
    write('audio_font.wav', fs, sr.astype(np.float32))

# Interface gráfica
def main(page: ft.Page):

    # Ajustar elementos quando redimensionar janela
    def page_resized(e):
        if control.content.controls[0].visible:
            page.remove(audio)
            transmitir(msg.controls[0].value,page.width/75,page.height/100,freqs.controls[0].controls[2].value,freqs.controls[1].controls[2].value)
            page.add(audio)
            page.update()
        else:
            page.update()

    # Preparar gráficos e arquivo de áudio e exibir elementos relevantes quando pressionar "Preparar Transmissão"
    def on_click_transmitir(e):
        if msg.controls[0].value != "":
            page.remove(audio) # é preciso remover o elemento de áudio da interface antes de atualizar o arquivo .wav por motivos de permissão de acesso
            transmitir(msg.controls[0].value,page.width/75,page.height/100,freqs.controls[0].controls[2].value,freqs.controls[1].controls[2].value)
            grafcon.visible = True # imagem só é visível após preparar transmissão
            control.content.controls[0].visible=True # botões de áudio somente visíveis após preparar transmissão
            page.add(audio)
            page.update()

    # Atualizar o valor de f0 e alterar os elementos quando mudar a posição do primeiro slider
    def f0_change(e):
        t0.value = f"{e.control.value:.0f}"
        if msg.controls[0].value != "":
            page.remove(audio)
            transmitir(msg.controls[0].value,page.width/75,page.height/100,freqs.controls[0].controls[2].value,freqs.controls[1].controls[2].value)
            page.add(audio)
        page.update()

    # Atualizar o valor de f1 e alterar os elementos quando mudar a posição do segundo slider
    def f1_change(e):
        t1.value = f"{e.control.value:.0f}"
        if msg.controls[0].value != "":
            page.remove(audio)
            transmitir(msg.controls[0].value,page.width/75,page.height/100,freqs.controls[0].controls[2].value,freqs.controls[1].controls[2].value)
            page.add(audio)
        page.update()

    page.window.maximized = True # Abrir interface maximizada
    page.title = "Transmissão BFSK"

    # fileira de elementos com campo de texto e botão de preparar transmissão
    msg = ft.Row(
        [
            ft.TextField(hint_text = "Digite a mensagem a ser transmitida",expand=True),
            ft.ElevatedButton(
            text = "Preparar Transmissão",
            on_click = on_click_transmitir,
            ),
        ],
    )

    audio = ft.Audio(src="audio_font.wav", autoplay = False)

    # Botões de áudio
    play = ft.ElevatedButton("Play", on_click=lambda _: audio.resume(),expand=True)

    pause = ft.ElevatedButton("Pause", on_click=lambda _: audio.pause(),expand=True)

    replay = ft.ElevatedButton("Replay", on_click=lambda _: audio.play(),expand=True)

    # Container que serve de placeholder para o gráfico
    grafcon = ft.Container(
        ft.Image(
            src="graf.svg",
        ),
        alignment=ft.alignment.center,
        visible=False
    )

    # Fileira de elementos contendo os botões de áudio
    player = ft.Row(
        [play,pause,replay],
        expand=True,
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
        expand=True,
    )

    # Container contendo todos os elementos embaixo do gráfico para facilitar no dimensionamento
    control = ft.Container(
        ft.Row(
            [player,freqs],
            alignment=ft.alignment.center,
            expand=True,
        ),
        alignment=ft.alignment.center,
        expand=True,
    )

    control.content.controls[0].visible = False # botões de áudio invisíveis antes de preparar transmissão
    page.add(msg,grafcon,control,audio)
    page.on_resized = page_resized

ft.app(target=main)