class FileReader(object):

  def __init__(self, f = None, mode = 'nonoverlap'):
    self._modes = {
       'nonoverlap': self._nonoverlapread,
       'overlap': self._overlapread
    }
    self._filters = []
    self._f = f
    try:
      self._readf = self._modes[mode]
    except KeyError as e:
      raise FileReaderUnknownMode('Not supported mode %s. Supported modes: %s' % (mode, self._modes.keys()))

  @property
  def file(self):
    return self._f

  @file.setter
  def file(self, f):
    self._f = f

  def addFilter(self, fil):
    self._filters.append(fil)

  def read(self):
    self._readf()

  def _overlapread(self):
    for line in self._f:
      for fil in self._filters:
        fil.line(line)

  def _nonoverlapread(self):
    for line in self._f:
      for fil in self._filters:
        match = fil.line(line)
        if match:
          break


class UnknownMode(Exception):
  pass
