from creeper import app
import sys

if __name__ == '__main__':
  if len(sys.argv) > 1:
    app.run(host='0.0.0.0', port=80)
  else:
    app.run()