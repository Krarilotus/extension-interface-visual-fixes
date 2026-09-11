"""Rendering-order regressions using emitted x86 and synthetic draw terminals."""
import struct
import pytest
from unicorn import UC_HOOK_CODE
from unicorn.x86_const import *
from test_tower_door_height import execute, expected, DEPTH, DEPTH_EPOCH, STACK, STOP, DRAW, BUILDING, render_address

def deferred_context(frame=81):
    c=execute(frame=frame,ground=104,walls=((1,-36,0x100),),foundation=True,painted=False,context=True)
    assert c['first_xy'] is None
    u=c['uc'];u.hook_del(c['draw_hook'])
    events=[]
    def terminal(uc,at,_size,_data):
        if at==0x453b00:events.append(('column',struct.unpack('<i',u.mem_read(0xed3178,4))[0]))
        else:
            sp=u.reg_read(UC_X86_REG_ESP)
            events.append(('door',*struct.unpack('<4i',u.mem_read(sp+4,16))))
    u.hook_add(UC_HOOK_CODE,terminal,begin=0x453b00,end=0x453b00)
    u.hook_add(UC_HOOK_CODE,terminal,begin=DRAW,end=DRAW)
    u.mem_write(0x453b00,b'\xc3')
    c['events']=events
    return c

def column(c,x,mask=2,owner=1):
    u=c['uc'];tile=c['tile'](206,89)
    u.mem_write(0x1c95bb8+tile*2,struct.pack('<H',owner))
    u.mem_write(0xed3178,struct.pack('<i',x));u.mem_write(0xed317c,struct.pack('<I',mask))
    u.mem_write(0xed3158,struct.pack('<I',7));u.mem_write(0xed3180,struct.pack('<I',123))
    u.mem_write(0xdf33a0,struct.pack('<H',0x4567))
    for r,v in zip(c['registers'],c['before']):u.reg_write(r,v)
    u.reg_write(UC_X86_REG_EBP,tile)
    before={r:u.reg_read(r) for r in c['registers']}
    u.emu_start(0x4eba52,0x4eba57,count=500)
    assert {r:u.reg_read(r) for r in c['registers']}==before
    assert struct.unpack('<I',u.mem_read(0xed3158,4))[0]==7
    assert struct.unpack('<I',u.mem_read(0xed3180,4))[0]==123
    assert struct.unpack('<H',u.mem_read(0xdf33a0,2))[0]==0x4567
    return c['events']

@pytest.mark.parametrize('frame,mask',[(81,2),(90,1)])
def test_lower_door_waits_for_its_backing_column_and_draws_exactly_once(frame,mask):
    c=deferred_context(frame);x,y=expected(frame=frame,index=1,rise=-36)
    threshold=x+20-16 if frame==81 else x-14
    column(c,threshold,mask,owner=0)
    column(c,threshold+(-1 if frame==81 else 1),mask)
    assert all(e[0]=='column' for e in c['events'])
    column(c,threshold,mask)
    assert c['events'][-2:]==[('column',threshold),('door',54,frame,x,y)]
    column(c,threshold,mask)
    assert len([e for e in c['events'] if e[0]=='door'])==1

@pytest.mark.parametrize('frame,mask',[(81,2),(90,1)])
def test_frame_transition_discards_a_clipped_pending_door(frame,mask):
    c=deferred_context(frame);u=c['uc']
    u.reg_write(UC_X86_REG_ESP,STACK)
    u.emu_start(0x4e8cf0,0x4e8cf8,count=40)
    assert struct.unpack('<I',u.mem_read(DEPTH_EPOCH,4))[0]==2
    column(c,1000 if frame==81 else -1000,mask)
    assert all(e[0]=='column' for e in c['events'])

@pytest.mark.parametrize('frame',[81,90])
def test_already_painted_foundation_preserves_original_draw(frame):
    c=execute(frame=frame,ground=104,walls=((1,-36,0x100),),foundation=True,context=True)
    assert c['first_xy']==expected(frame=frame,index=1,rise=-36)
    assert struct.unpack('<I',c['uc'].mem_read(DEPTH+203*40+12,4))[0]==0
