from sqlalchemy import Enum

matches_types = ('Pre-Season', 'Season', 'Post-Season')

vars_ = locals().copy()
for k, v in vars_.items():
    if isinstance(v, tuple):
        locals()[k] = Enum(*v, name=k)
