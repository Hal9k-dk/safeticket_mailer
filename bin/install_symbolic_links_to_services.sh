#!/usr/bin/env bash
# ex: set tabstop=8 softtabstop=0 expandtab shiftwidth=2 smarttab:

if [ ! -d .git ]; then
  echo The working directory have to the root directory of the git project
  exit 1
fi

set -eu

FOLDER="${HOME}/.config/systemd/user"
mkdir -p "${FOLDER}"

for file in "${FOLDER}"/*.{service,timer}; do
  if [ -L "${file}" ]; then
    if [ ! -e "${file}" ]; then
      rm "${_file}"
    fi
  fi
done

for file in ${PWD}/systemd.service/*.{service,timer}; do
  if [ -f "${file}" ] && [ ! -e "${FOLDER}"/$(basename "${file}") ]; then
    ln -s "${file}" "${FOLDER}"/$(basename "${file}")
  fi
done
