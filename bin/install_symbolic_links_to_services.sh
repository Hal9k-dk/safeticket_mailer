#!/usr/bin/env bash
# ex: set tabstop=8 softtabstop=0 expandtab shiftwidth=2 smarttab:

set -eu

mkdir -p ~/.config/systemd/user

for file in ~/.config/systemd/user/*.{service,timer}; do
  if [ -L "${file}" ]; then
    if [ ! -e "${file}" ]; then
      rm "${_file}"
    fi
  fi
done

for file in ${PWD}/systemd.service/*.{service,timer}; do
  if [ -f "${file}" ] && [ ! -e ~/.config/systemd/user/$(basename "${file}") ]; then
    ln -s "${file}" ~/.config/systemd/user/$(basename "${file}")
  fi
done

