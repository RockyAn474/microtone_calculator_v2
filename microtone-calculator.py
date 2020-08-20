import tkinter as tk
import math
import numpy as np
import pyaudio
import time


FRET_COUNT = 19
##In millimeters
SCALE_LENGTH = 650
NUT_WIDTH = 52
FRET_THICKNESS = 2
#In Hz
STANDARD_A4 = 440

#Frets below A4 for each string ***MUST BE ORDERED***
OPEN_STRING_SCALE = [17, 12, 7, 2, -2, -7]
twelve_TET_list = ['\n\n\n\n\n'+'A','A#'+'\n\n'+'Bb','\n\n\n\n\n'+'B','\n\n\n\n\n'+'C','C#'+'\n\n'+'Db','\n\n\n\n\n'+'D','D#'
                   +'\n\n'+'Eb','\n\n\n\n\n'+'E','\n\n\n\n\n'+'F','F#'+'\n\n'+'Gb','\n\n\n\n\n'+'G','G#'+'\n\n'+'Ab']
twelve_TET_list_ns = ['A','A#/Bb','B','C','C#/Db','D','D#/Eb','E','F','F#/Gb','G','G#/Ab']

COLORLIST = ["red", "orange", "#9b870c", "green", "blue", "indigo", "violet"]
COLORINDEX = 0
STRINGLIST = ["Low E", "A", "D", "G", "B", "High e"]
#COLORLIST_VAR=(red,orange,yellow,green,blue,indigo,violet)

#Pixels
WINDOW_WIDTH = 550
WINDOW_HEIGHT = 1000
CANVAS_WIDTH = 200
CANVAS_HEIGHT = 1000/1.5
CANVAS_MARGIN_HEIGHT = 12
BUTTON_OFFSET = 110

#Pixels per millimeter
CANVAS_SCALE = 1.5
CANVAS_WIDTH*=CANVAS_SCALE
CANVAS_HEIGHT*=CANVAS_SCALE
WINDOW_WIDTH=int((CANVAS_SCALE/1.5)*WINDOW_WIDTH)
FRET_THICKNESS*=CANVAS_SCALE

'''Global Variables'''
counter = 0
g_black_keys_index = [7, 8, 9, 10, 11]
g_white_keys_index = [0, 1, 2, 3, 4, 5, 6]
focus_note_num = []
g_interval = 1
play_freqlist = []


def drop_D(D):
    if D is True:
        OPEN_STRING_SCALE[0]+=2

def position(fret=0,cents=0):
    """Length in  millimeters from nut"""
    return SCALE_LENGTH - SCALE_LENGTH/(2**((fret+cents/100)/12))

def inv_position(y1,y2):
    '''Inverse of position, pos is millimeters from nut'''
    pos=(y1+y2)/2
    if SCALE_LENGTH == pos:
        return 0
    else:
        return 12*math.log2((SCALE_LENGTH)/(SCALE_LENGTH-pos))

def fret_normalize(x1,x2,fret):
    '''Normalize fret based on string, give x coordinate range, and unnormalized fret'''
    avg=(x1+x2)/2
    temp_list = []
    for stri_num in range(len(OPEN_STRING_SCALE)):
        temp_list.append((CANVAS_WIDTH - CANVAS_SCALE * NUT_WIDTH) / 2 + CANVAS_SCALE * stri_num * NUT_WIDTH / len(OPEN_STRING_SCALE))
    temp_list.append(avg)
    temp_list.sort()
    return fret-OPEN_STRING_SCALE[(temp_list.index(avg)-1)]


def freq_to_fret(freq,compare=STANDARD_A4):
    '''How many half_step (fret) away from a note (default A4'''
    return math.log2(freq/compare)*12

def fret_to_freq(fret,compare=STANDARD_A4):
    '''Inverse of freq_to_fret'''
    return compare * 2 ** (fret / 12)

def interval(fret,base_fret):
    '''interal based of half-step difference, warning kinda broken'''
    temp = 2 ** ((fret - base_fret-24) /12)
    if temp <1:
        #reciprocate
        temp=1/temp
    while temp >2:
        temp*=0.5
    return temp

def find_microtones(note_num):
    '''Returns ordered coord list [fret,string] of the microtones'''
    global COLORINDEX
    global focus_note_num
    global g_interval
    freqs_spanned = []
    freq = (fret_to_freq(note_num))
    maxfreq = fret_to_freq(FRET_COUNT - OPEN_STRING_SCALE[-1])
    minfreq = fret_to_freq(-OPEN_STRING_SCALE[0])
    spectrum = []
    freq *= int(app.limit_entry_result.get())
    try:
        intv = interval(note_num,g_interval)
        app.harmonic_info.delete(0,'end')
        app.harmonic_info.insert(0,str(round(intv,3))+' from '+twelve_TET_list_ns[note_num])
    except:
        pass
    while freq > maxfreq+2:
        freq/=2
    while freq > minfreq:
        freqs_spanned.append(freq)
        freq/=2


        freqs_spanned.append((freq))
    for stri in range(len(OPEN_STRING_SCALE)):
        for freq in freqs_spanned:
            f = freq_to_fret(freq) + OPEN_STRING_SCALE[stri]
            if f < FRET_COUNT and f > 0:
                spectrum.append(f)
                spectrum.append(stri)
            elif f < FRET_COUNT-12 and f > 0:
                f+=12
                spectrum.append(f)
                spectrum.append(f)
    #colorindex[colour]['text'] = frets
    COLORINDEX += 1
    COLORINDEX %= 7
    focus_note_num.append(note_num)
    return spectrum

def draw_frets_custom(note_num):
    if True:
        rank_two_list = find_microtones(note_num)
        for x in range(len(rank_two_list)):
            if (x % 2) == 0:
                app.unsaved_fretlist.append(app.canvas.create_rectangle((CANVAS_WIDTH-CANVAS_SCALE*NUT_WIDTH)/2+CANVAS_SCALE*rank_two_list[x+1]*NUT_WIDTH/len(OPEN_STRING_SCALE),
                                                                 CANVAS_SCALE*(CANVAS_MARGIN_HEIGHT + position(rank_two_list[x])-FRET_THICKNESS/3),
                                                                 (
                                                                             CANVAS_WIDTH - CANVAS_SCALE * NUT_WIDTH) / 2 + CANVAS_SCALE *
                                                                 (rank_two_list[x + 1]+1) * NUT_WIDTH / len(
                                                                     OPEN_STRING_SCALE),CANVAS_SCALE*(CANVAS_MARGIN_HEIGHT + position(rank_two_list[x])+FRET_THICKNESS/3),
                                           fill=COLORLIST[COLORINDEX-1],activefill='black', width=0,tag=('fret',round(rank_two_list[x]),rank_two_list[x+1],note_num,app.limit_entry_result.get(),'unsaved')))



def locate_fret(y1,y2,next=True):
    'locate fret y position in terms of frets'
    avg=(y1+y2)/2
    temp_list = []
    for fret in app.DEFAULT_FRETLIST:
        diff = avg-((app.canvas.coords(fret)[1]+app.canvas.coords(fret)[3])/2)
        if diff >=0 and next==False:
            temp_list.append(diff)
        if diff <=0 and next==True:
            temp_list.append(diff)
    return min(temp_list) if next ==False else max(temp_list)*-1

def select_fret(event):
    '''Selects fret on click, sorry this is really confusing djsadsakjca'''
    frettags = (app.canvas.gettags(app.canvas.find_withtag('current')))
    if 'unsaved' in frettags:
        app.canvas.itemconfig(app.canvas.find_withtag('current'), width=FRET_THICKNESS*0.9)
        app.canvas.update_idletasks()
        app.canvas.after(150)
        app.canvas.itemconfig(app.canvas.find_withtag('current'), width=0)
        fill = app.canvas.itemcget(app.canvas.find_withtag('current'),'fill')
        activefill = app.canvas.itemcget(app.canvas.find_withtag('current'), 'activefill')
        app.canvas.itemconfig('current', fill=activefill,activefill=fill,outline=fill, tag=('fret',frettags[1],frettags[2],frettags[3],frettags[4],'saved','current'))

    elif 'saved' in frettags:
        app.canvas.itemconfig(app.canvas.find_withtag('current'), width=FRET_THICKNESS*0.9)
        app.canvas.update_idletasks()
        app.canvas.after(200)
        app.canvas.itemconfig(app.canvas.find_withtag('current'), width=0)
        fill = app.canvas.itemcget(app.canvas.find_withtag('current'),'fill')
        activefill = app.canvas.itemcget(app.canvas.find_withtag('current'), 'activefill')
        app.canvas.itemconfig('current', fill=activefill,activefill=fill,outline = activefill,tag=('fret',frettags[1],frettags[2],frettags[3],frettags[4],'unsaved','current'))
def select_fret_alt(event):
    '''Selects fret on click, sorry this is really confusing djsadsakjca'''
    frettags = (app.canvas.gettags(app.canvas.find_withtag('current')))
    if 'fret' in frettags and not 'saved_alt' in frettags:
        app.canvas.itemconfig(app.canvas.find_withtag('current'), width=FRET_THICKNESS*0.5)
        app.canvas.update_idletasks()
        app.canvas.after(100)
        app.canvas.itemconfig(app.canvas.find_withtag('current'), width=FRET_THICKNESS)
        fill = app.canvas.itemcget(app.canvas.find_withtag('current'),'fill')
        activefill = app.canvas.itemcget(app.canvas.find_withtag('current'), 'activefill')
        coord_tup = (app.canvas.coords(app.canvas.find_withtag('current')))
        inv_pos = inv_position(coord_tup[1] / CANVAS_SCALE - CANVAS_MARGIN_HEIGHT
                               , coord_tup[3] / CANVAS_SCALE - CANVAS_MARGIN_HEIGHT)
        fret_normal = fret_normalize(coord_tup[0], coord_tup[2], inv_pos)%12
        draw_frets_custom(fret_normal)
        if app.canvas.find_withtag('saved_alt'):
            fill2 = app.canvas.itemcget(app.canvas.find_withtag('saved_alt'), 'fill')
            activefill2 = app.canvas.itemcget(app.canvas.find_withtag('saved_alt'), 'activefill')
            app.canvas.itemconfig(app.canvas.find_withtag('saved_alt'), fill=activefill2,activefill=fill2,outline=fill2,width=0)
            app.canvas.dtag(app.canvas.find_withtag('saved_alt'),'saved_alt')
        try:
            app.canvas.itemconfig('current', fill=activefill,activefill=fill,outline=fill, tag=('fret',frettags[1],frettags[2],frettags[3],frettags[4],frettags[5],'saved_alt'))
        except:
            app.canvas.itemconfig('current', fill=activefill,activefill=fill,outline=fill, tag=('fret',frettags[1],frettags[2],frettags[3],'saved_alt'))

    elif 'saved_alt' in frettags:
        frettags = (app.canvas.gettags(app.canvas.find_withtag('current')))
        if 'unsaved' in frettags:
            app.canvas.itemconfig(app.canvas.find_withtag('current'), width=FRET_THICKNESS * 0.9)
            app.canvas.update_idletasks()
            app.canvas.after(150)
            app.canvas.itemconfig(app.canvas.find_withtag('current'), width=0)
            fill = app.canvas.itemcget(app.canvas.find_withtag('current'), 'fill')
            activefill = app.canvas.itemcget(app.canvas.find_withtag('current'), 'activefill')
            app.canvas.itemconfig('current', fill=activefill, activefill=fill, outline=fill,
                                  tag=('fret', frettags[1], frettags[2], frettags[3], frettags[4], 'saved', 'current'))

        elif 'saved' in frettags:
            app.canvas.itemconfig(app.canvas.find_withtag('current'), width=FRET_THICKNESS * 0.9)
            app.canvas.update_idletasks()
            app.canvas.after(200)
            app.canvas.itemconfig(app.canvas.find_withtag('current'), width=0)
            fill = app.canvas.itemcget(app.canvas.find_withtag('current'), 'fill')
            activefill = app.canvas.itemcget(app.canvas.find_withtag('current'), 'activefill')
            app.canvas.itemconfig('current', fill=activefill, activefill=fill, outline=activefill, tag=(
            'fret', frettags[1], frettags[2], frettags[3], frettags[4], 'unsaved', 'current'))

    ##print((app.canvas.gettags(app.canvas.find_withtag('current'))))

def select_play(event):
    global play_freqlist
    '''Selects fret on click, sorry this is really confusing djsadsakjca'''
    frettags = (app.canvas.gettags(app.canvas.find_withtag('current')))
    if not 'unplay' in frettags:
        app.canvas.itemconfig(app.canvas.find_withtag('current'), width=FRET_THICKNESS*0.9)
        app.canvas.update_idletasks()
        app.canvas.after(150)
        app.canvas.itemconfig(app.canvas.find_withtag('current'), width=0)
        fill = app.canvas.itemcget(app.canvas.find_withtag('current'),'fill')
        activefill = app.canvas.itemcget(app.canvas.find_withtag('current'), 'activefill')
        #app.canvas.itemconfig('current', fill='yellow',activefill=fill,outline=fill, tag=('fret',frettags[1],frettags[2],frettags[3],frettags[4],'play','current'))
        play_freqlist.append(float(app.frequency.get()))
        print (play_freqlist)

def toggle_colors():
    '''toggles fret colors on click, sorry this is really confusing djsadsakjca but its badass'''
    for fret in app.unsaved_fretlist:
        if 'unsaved' in app.canvas.gettags(fret):
            #app.canvas.itemconfig(fret, width=FRET_THICKNESS * 0.9)
            #app.canvas.update_idletasks()
            #app.canvas.after(150)
            #app.canvas.itemconfig(fret, width=0)
            fill = app.canvas.itemcget(fret, 'fill')
            activefill = app.canvas.itemcget(fret, 'activefill')
            app.canvas.itemconfig(fret, fill=activefill,activefill=fill)
        elif 'saved' in app.canvas.gettags(fret):
            #app.canvas.itemconfig(fret, width=FRET_THICKNESS * 0.9)
            #app.canvas.update_idletasks()
            #app.canvas.after(200)
            #app.canvas.itemconfig(fret, width=0)
            fill = app.canvas.itemcget(fret, 'fill')
            activefill = app.canvas.itemcget(fret, 'activefill')
            app.canvas.itemconfig(fret, fill=activefill,activefill=fill)
def callback(in_data, frame_count, time_info, status):
    return (in_data, pyaudio.paContinue)


def playsine():
    p = pyaudio.PyAudio()
    volume = 1 / (len(play_freqlist))  # range [0.0, 1.0]
    fs = 44100  # sampling rate, Hz, must be integer
    duration = 10  # in seconds, may be float
    f = play_freqlist  # sine frequency, Hz, may be float
    # generate samples, note conversion to float32 array
    samples = np.sin(2 * np.pi * np.arange(fs * duration) * f[0] / fs).astype(np.float32)
    for freeks in play_freqlist[1:]:
        samples += np.sin(2 * np.pi * np.arange(fs * duration) * freeks / fs).astype(np.float32)

    # for paFloat32 sample values must be in range [-1.0, 1.0]
    stream = p.open(format=pyaudio.paFloat32,
                    channels=1,
                    rate=fs,
                    output=True,
                    )

    # play. May repeat with different volume values (if done interactively)
    stream.write(volume * samples)
    stream.stop_stream()
    stream.close()

    p.terminate()
    play_freqlist.clear()
def graph_sine(selected_frets):
    """Graphs sine wave
    Attr. should be list of freqencies, flaot"""
    pass

def update_tool_tip(event):
    global focus_note_num
    global g_interval
    ordinal = lambda n: "%d%s" % (n, "tsnrhtdd"[(n // 10 % 10 != 1) * (n % 10 < 4) * n % 10::4])
    if app.canvas.find_withtag('current'):
        tags = app.canvas.gettags(app.canvas.find_withtag('current'))
        if 'fret' in tags:
            fret_ordered = (int(tags[1])-OPEN_STRING_SCALE[int(tags[2])])%12
            note = twelve_TET_list_ns[fret_ordered]
            coord_tup = (app.canvas.coords(app.canvas.find_withtag('current')))
            inv_pos = inv_position(coord_tup[1]/CANVAS_SCALE-CANVAS_MARGIN_HEIGHT
                                                                         ,coord_tup[3]/CANVAS_SCALE-CANVAS_MARGIN_HEIGHT)
            fret_normal =  (fret_normalize(coord_tup[0],coord_tup[2],inv_pos))
            app.note.delete(0,'end')
            app.harmonic_info.delete(0,'end')
            app.note.insert(0, note)
            if tags.count('unsaved') + tags.count('saved') != 0:
                #app.harmonic_info.insert(0,ordinal(int(tags[4]))+' harmonic of '+twelve_TET_list_ns[int(tags[3])])
                try:
                    app.note.insert(0,ordinal(int(tags[4]))+' harmonic of: '+twelve_TET_list_ns[int(tags[3])]+'     (~')
                except:
                    app.note.insert(0, ordinal(int(tags[4])) + ' harm. of: ' +
                        twelve_TET_list_ns[int(float(tags[3]))] +'+'+str(float(tags[3])%1)[2:4]+ 'cents     (~')
                app.note.insert('end',')')
            app.frequency.delete(0,'end')
            app.frequency.insert(0,round(fret_to_freq(fret_normal),5))
            app.harmonic_info.delete(0,'end')
            try:
                try:
                    g_interval = fret_normal
                    app.harmonic_info.insert(0,str(round(interval(focus_note_num[-1],fret_normal),3))+' from '+twelve_TET_list_ns[focus_note_num[-1]])
                except:
                    app.harmonic_info.insert(0,str(round(interval(focus_note_num[-1],fret_normal),3))+' from '+twelve_TET_list_ns[int(float(tags[3]))] +'+'+str(float(tags[3])%1)[2:4]+ 'cents')
            except:
                pass
            app.higher_dist.delete(0, 'end')
            app.higher_dist.insert(0, round((locate_fret(coord_tup[1],coord_tup[3],False)/CANVAS_SCALE),2))
            app.lower_dist.delete(0, 'end')
            app.lower_dist.insert(0, round((locate_fret(coord_tup[1],coord_tup[3],True)/CANVAS_SCALE),2))
            app.higher_cent.delete(0, 'end')
            app.higher_cent.insert(0, round(inv_pos*100%100,2))
            app.lower_cent.delete(0, 'end')
            app.lower_cent.insert(0, round(100-inv_pos*100%100,2))



def clear_unsaved_frets():
    global focus_note_num
    global g_black_keys_index
    global g_white_keys_index
    exists = True

    for fret in app.unsaved_fretlist:
        if 'unsaved' in app.canvas.gettags(fret):
            app.canvas.delete(fret)
        elif 'saved' in app.canvas.gettags(fret):
            exists = False
            #app.canvas.itemconfig(fret,tag=('saved', 'fret'))
            for note_num in focus_note_num:
                if note_num in g_black_keys_index:
                    g_black_keys_index.remove(note_num)
                if note_num in g_white_keys_index:
                    g_white_keys_index.remove(note_num)
    if exists == True:
        for button in range(len(app.piano_buttons)):
            if button in g_black_keys_index:
                app.piano_buttons[button].config(background='#222222')
            if button in g_white_keys_index:
                app.piano_buttons[button].config(background='white')


def clear_all_frets():
    global g_black_keys_index
    global g_white_keys_index
    black_keys_index = [7, 8, 9, 10, 11]
    white_keys_index = [0, 1, 2, 3, 4, 5, 6]
    for fret in app.unsaved_fretlist:
        app.canvas.delete(fret)
    for button in range(len(app.piano_buttons)):
        if button in black_keys_index:
            app.piano_buttons[button].config(background='#222222')
        if button in white_keys_index:
            app.piano_buttons[button].config(background='white')


class app_Label(tk.Label):
    '''Themed labels'''
    def __init__(self,text,x,y):
        label = tk.Label(
            text=text,
            font=("Helvetica", 12,'bold'),
            justify='left'
            )
        label.place(x=x+CANVAS_MARGIN_HEIGHT, y=y)


class arrow_button(tk.Button):
    '''Select a note A to G'''
    def __init__(self,change,y=280):
        text = ''
        offset=0
        if change == -1:
            text = '<-'
        elif change == 1:
            text = '->'
            offset+=BUTTON_OFFSET
        button = tk.Button(
            text=text,
            width=10,
            height=2,
            bg="white",
            fg="black",
            font=("Helvetica", 12, 'bold'),
            command=lambda: app.change_limit_label(self,change)
            )
        button.place(x=CANVAS_MARGIN_HEIGHT+offset, y=y)

class clear_button(tk.Button):
    '''Clear'''
    def __init__(self,command,x=0,y=900,text='Clear'):
        button = tk.Button(
            text=text,
            width=10,
            height=2,
            bg="white",
            fg="black",
            font=("Helvetica", 12, 'bold'),
            command=command)
        button.place(x=CANVAS_MARGIN_HEIGHT+x, y=y)

class app(object):
    DEFAULT_FRETLIST = []
    unsaved_fretlist = []
    piano_buttons = []
    clear = None
    piano_l =  []
    def __init__(self):
        app.window = tk.Tk()
        app.window.minsize(WINDOW_WIDTH, WINDOW_HEIGHT)
        app.window.title("Microtone Calculator")
        app.canvas = tk.Canvas(app.window, width=CANVAS_WIDTH, height=CANVAS_HEIGHT, bg='white',closeenough=3)
        app.canvas.place(x=WINDOW_WIDTH-CANVAS_WIDTH, y=0)
        app.DEFAULT_FRETLIST = app.draw_guitar(self,app.canvas)
        app.draw_note_buttons(self)
        app.piano_l = app_Label('Select Base Note',0,70)
        limit_label = app_Label("Harmonic:",0,250)
        app.limit_entry_result = tk.Entry()
        app.limit_entry_result.insert(0, 4)
        app.limit_entry_result.place(x=100,y=253)
        app.note = tk.Entry()
        app.note.place(x=65,y=328+25,width=170)
        app.frequency = tk.Entry()
        app.frequency.place(x=110,y=353+25)
        app.harmonic_info = tk.Entry()
        app.harmonic_info.place(x=110,y=403)
        app.higher_cent = tk.Entry()
        app.higher_cent.place(x=110,y=428+50)
        app.higher_dist = tk.Entry()
        app.higher_dist.place(x=110,y=453+50)
        app.lower_cent = tk.Entry()
        app.lower_cent.place(x=110,y=528+50)
        app.lower_dist = tk.Entry()
        app.lower_dist.place(x=110,y=553+50)
        app.change_limit_label(self,1)
        arrow_button(1)
        arrow_button(-1)
        app.clear = clear_button(lambda: clear_unsaved_frets(),text='Clear'+'\n'+'Unsaved')
        clear_button(lambda: clear_all_frets(),x=BUTTON_OFFSET,text='Clear'+'\n'+'All')
        clear_button(lambda: app.clear_default_frets(self, app.canvas), x=BUTTON_OFFSET, text='Toggle' + '\n' + 'Frets',y=848)
        clear_button(lambda: toggle_colors(), x=0, text='Toggle' + '\n' + 'Colors',
                     y=848)
        clear_button(lambda: playsine(), x=0, text='Play',
                     y=00)

        app.canvas.bind("<Button-1>", select_fret)
        app.canvas.bind("<Button-3>", select_fret_alt)
        app.canvas.bind("<Control-Button-1>", select_play)
        app.canvas.bind('<Motion>', update_tool_tip)
        app.info = app_Label('Note:',0,350)
        app.info = app_Label('Frequency:', 0, 375)
        app.info = app_Label('Interval:', 0, 400)
        app.info = app_Label('Distance from Previous Fret', 0, 450)
        app.info = app_Label('Cents:', 0, 475)
        app.info = app_Label('Millimeters:', 0, 500)
        app.info = app_Label('Distance to Next Fret', 0, 550)
        app.info = app_Label('Cents:', 0, 575)
        app.info = app_Label('Millimeters:', 0, 600)
        app.window.mainloop()

    def draw_note_buttons(self):
        '''Places 12 tone buttons'''
        for note_num in [0, 2, 3, 5, 7, 8, 10]:
            app.piano_buttons.append(app.create_note_button(self,note_num))
        for note_num in [1, 4, 6, 9, 11]:
            app.piano_buttons.append(app.create_note_button(self,note_num))

    def change_limit_label(self,change=1):
        '''Change the harmonic'''
        temp = int(app.limit_entry_result.get())
        temp+=change
        if temp >2:
            app.limit_entry_result.delete(0,'end')
            app.limit_entry_result.insert(0,temp)

    def draw_default_frets(self,canvas):
        fretlist = []
        fretlindex = 0
        for stri_num in range(len(OPEN_STRING_SCALE)):
            for fret_num in range(FRET_COUNT + 1):
                fretlist.append(
                    canvas.create_rectangle((CANVAS_WIDTH-CANVAS_SCALE*NUT_WIDTH)/2+CANVAS_SCALE*stri_num*NUT_WIDTH/len(OPEN_STRING_SCALE),
                                            CANVAS_SCALE*(CANVAS_MARGIN_HEIGHT + position(fret_num)-FRET_THICKNESS/3)
                                            ,(CANVAS_WIDTH-CANVAS_SCALE*NUT_WIDTH)/2+CANVAS_SCALE*(stri_num+1)*NUT_WIDTH/len(OPEN_STRING_SCALE),
                                            CANVAS_SCALE*(CANVAS_MARGIN_HEIGHT + position(fret_num)+FRET_THICKNESS/3),
                                            fill="#333333",activefill='#666666',
                                            width=0, tag=('fret',fretlindex%(FRET_COUNT+1),fretlindex//(FRET_COUNT+1))))
                fretlindex+=1

                if stri_num == 0:
                    temp_text = canvas.create_text((CANVAS_WIDTH-CANVAS_SCALE*NUT_WIDTH)/2-CANVAS_MARGIN_HEIGHT*CANVAS_SCALE
                               , CANVAS_SCALE*(CANVAS_MARGIN_HEIGHT + position(fret_num)), text=fret_num, font=("Ariel", 10), justify='right')
                    if fret_num == 12:
                        canvas.move(temp_text,0,-FRET_THICKNESS)
        return fretlist

    def clear_default_frets(self,canvas):
        global counter
        if counter % 2 == 0:
            for fret in app.DEFAULT_FRETLIST:
                if 'fret' in app.canvas.gettags(fret):
                    app.canvas.itemconfig(fret,fill='white')
        else:
            for fret in app.DEFAULT_FRETLIST:
                if 'fret' in app.canvas.gettags(fret):
                    app.canvas.itemconfig(fret, fill='black')
        counter += 1

    def draw_guitar(self,canvas):
        '''Draws guitar and returns list of default fret objects'''

        body = canvas.create_arc(-10*CANVAS_SCALE, CANVAS_SCALE*(CANVAS_MARGIN_HEIGHT + position(12)), CANVAS_WIDTH+10*CANVAS_SCALE,
                                 CANVAS_SCALE*(CANVAS_MARGIN_HEIGHT + position(12) + 80), start=00,
                     extent=180, outline="black", fill="white", width=2)
        body_block = canvas.create_rectangle(0, CANVAS_SCALE*(CANVAS_MARGIN_HEIGHT + position(12) + 40),
                                             CANVAS_WIDTH+2, (position(12) + CANVAS_MARGIN_HEIGHT+44)*CANVAS_SCALE,
                           outline="white", fill="white", width=2)
        bridge = canvas.create_rectangle(CANVAS_WIDTH/2-NUT_WIDTH*CANVAS_SCALE/2-31*CANVAS_SCALE, CANVAS_SCALE*(SCALE_LENGTH+CANVAS_MARGIN_HEIGHT-5),
                                         CANVAS_WIDTH/2+NUT_WIDTH*CANVAS_SCALE/2+30*CANVAS_SCALE,CANVAS_SCALE*(SCALE_LENGTH+CANVAS_MARGIN_HEIGHT+5),
                           outline="white", fill="#996600")
        head = canvas.create_rectangle(CANVAS_WIDTH/2-NUT_WIDTH*CANVAS_SCALE/2-5*CANVAS_SCALE, 0,
                                       CANVAS_WIDTH/2+NUT_WIDTH*CANVAS_SCALE/2+5*CANVAS_SCALE-2, CANVAS_MARGIN_HEIGHT*CANVAS_SCALE,
                          outline="white", fill="#996600")
        soundhole = canvas.create_oval(CANVAS_WIDTH/2 - CANVAS_SCALE*(position(28.2) - position(18.7))/2, CANVAS_SCALE*(CANVAS_MARGIN_HEIGHT + position(18.7)),
                                       CANVAS_WIDTH/2 + CANVAS_SCALE*(position(28.2) - position(18.7))/2,CANVAS_SCALE*(CANVAS_MARGIN_HEIGHT + position(28.2)),
                      outline="#996600", fill="#2b2b2f", width=4)
        for string_num in range(len(OPEN_STRING_SCALE)):
            canvas.create_line((CANVAS_WIDTH-CANVAS_SCALE*NUT_WIDTH)/2+(string_num+ 0.5) * NUT_WIDTH*CANVAS_SCALE//(len(OPEN_STRING_SCALE)),
                                CANVAS_MARGIN_HEIGHT*CANVAS_SCALE,(CANVAS_WIDTH-CANVAS_SCALE*NUT_WIDTH)/2+(string_num+ 0.5) *
                                                                   NUT_WIDTH*CANVAS_SCALE//(len(OPEN_STRING_SCALE)), (CANVAS_MARGIN_HEIGHT+SCALE_LENGTH)*CANVAS_SCALE,
                          fill="grey")
        fretlist = app.draw_default_frets(self,canvas)

        saddle = canvas.create_rectangle((CANVAS_WIDTH-CANVAS_SCALE*NUT_WIDTH)/2, CANVAS_SCALE*(CANVAS_MARGIN_HEIGHT + SCALE_LENGTH-FRET_THICKNESS/3)
                                        ,(CANVAS_WIDTH+CANVAS_SCALE*NUT_WIDTH)/2, CANVAS_SCALE*(CANVAS_MARGIN_HEIGHT + SCALE_LENGTH+FRET_THICKNESS/3),
                                        fill="black",
                                        width=0, tag='fret')
        return fretlist



    def draw_frets(self,note_num):
        rank_two_list = find_microtones(note_num)
        oops = [0,7,1,2,8,3,9,4,5,10,6,11]
        for x in range(len(rank_two_list)):
            if (x % 2) == 0:
                app.unsaved_fretlist.append(app.canvas.create_rectangle((CANVAS_WIDTH-CANVAS_SCALE*NUT_WIDTH)/2+CANVAS_SCALE*rank_two_list[x+1]*NUT_WIDTH/len(OPEN_STRING_SCALE),
                                                                 CANVAS_SCALE*(CANVAS_MARGIN_HEIGHT + position(rank_two_list[x])-FRET_THICKNESS/3),
                                                                 (
                                                                             CANVAS_WIDTH - CANVAS_SCALE * NUT_WIDTH) / 2 + CANVAS_SCALE *
                                                                 (rank_two_list[x + 1]+1) * NUT_WIDTH / len(
                                                                     OPEN_STRING_SCALE),CANVAS_SCALE*(CANVAS_MARGIN_HEIGHT + position(rank_two_list[x])+FRET_THICKNESS/3),
                                           fill=COLORLIST[COLORINDEX-1],activefill='black', width=0,tag=('fret',round(rank_two_list[x]),rank_two_list[x+1],note_num,app.limit_entry_result.get(),'unsaved')))
        app.piano_buttons[oops[note_num]].config(background=COLORLIST[COLORINDEX-1])

    def create_note_button(self, note_num):
        '''Select a note A to G'''

        black_keys_index = [1, 4, 6, 9, 11]
        white_keys_index = [0, 2, 3, 5, 7, 8, 10]
        KEY_SPACING = 32
        if True:
            if note_num in black_keys_index:
                button = tk.Button(
                    text=twelve_TET_list[note_num],
                    width=2,
                    height=5,
                    bg="#222222",
                    fg="white",
                    activebackground='#333333',
                    command=lambda: app.draw_frets(self,note_num)
                )
                piano_pos = black_keys_index.index(note_num)
                if piano_pos >= 1 and piano_pos < 3:
                    piano_pos += 1
                elif piano_pos >= 3:
                    piano_pos += 2
                if piano_pos == 0 or piano_pos == 1:
                    piano_pos += 7
                button.place(x=-4 * CANVAS_MARGIN_HEIGHT + (piano_pos + 0.5) * KEY_SPACING, y=100)

            elif note_num in white_keys_index:
                piano_pos = white_keys_index.index(note_num)
                if piano_pos == 0 or piano_pos == 1:
                    piano_pos += 7
                button = tk.Button(
                    text=twelve_TET_list[note_num],
                    width=3,
                    height=8,
                    bg="white",
                    fg="black",
                    command=lambda: app.draw_frets(self, note_num)
                )
                button.place(x=-4.2 * CANVAS_MARGIN_HEIGHT + piano_pos * KEY_SPACING, y=100)
        return button

    def highlight_saved_alt(self):

            print('yes')
            app.canvas.itemconfig(app.canvas.find_withtag('saved_alt'), width=FRET_THICKNESS * 0.5)
            app.canvas.update_idletasks()
            app.canvas.after(150)
            app.canvas.itemconfig(app.canvas.find_withtag('saved_alt'), width=FRET_THICKNESS)
    #def zoom(self):
        #global CANVAS_SCALE
        #app.window.destroy()
        #CANVAS_SCALE += 0.5
        #app()
app()


