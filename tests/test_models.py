from rarapla.models.channel import Channel
from rarapla.models.program import Program

def test_channel_model_basic() -> None:
    ch = Channel('FMT', 'FM TOKYO', 'http://cdn/logo.png', 'NOW', 'http://img.png')
    assert ch.id == 'FMT'
    assert ch.name == 'FM TOKYO'
    assert ch.program_title == 'NOW'

def test_program_model_basic() -> None:
    p = Program('Title', pfm='A,B', desc='D', image='I')
    assert p.title == 'Title'
    assert p.pfm == 'A,B'
