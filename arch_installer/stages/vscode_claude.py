"""Установка VS Code и Claude Code.

Устанавливает Visual Studio Code из AUR через yay,
настраивает npm-префикс в домашней директории пользователя
и устанавливает Claude Code через npm.
"""

from __future__ import annotations

import time
from pathlib import Path

from ..constants import MOUNT_POINT
from ..exceptions import StageError
from ..utils.chroot import chroot_run, write_file_in_chroot
from .base_stage import BaseStage


class VsCodeClaudeStage(BaseStage):
    """Этап установки VS Code и Claude Code.

    Использует yay (установленный на предыдущем этапе) для
    установки VS Code из AUR. Claude Code устанавливается
    глобально через npm с пользовательским префиксом.
    """

    name = "VS Code и Claude Code"
    weight = 3
    skippable = True

    def run(self) -> None:
        """Установить VS Code и Claude Code.

        Raises:
            StageError: При ошибке установки пакетов.
        """
        self.ui.set_stage(self.name)

        if self.config.demo_mode:
            self._run_demo()
            return

        username = self.config.username

        # Установка VS Code из AUR через yay
        self._install_vscode(username)

        # Настройка npm-префикса и установка Claude Code
        self._install_claude_code(username)

        self.ui.log_success("VS Code и Claude Code установлены")

    def _install_vscode(self, username: str) -> None:
        """Установка Visual Studio Code из AUR.

        Args:
            username: Имя пользователя для запуска yay.
        """
        # Временная настройка sudo без пароля для yay
        tmp_sudoers = MOUNT_POINT / "etc" / "sudoers.d" / "99-vscode-build"
        tmp_sudoers.parent.mkdir(parents=True, exist_ok=True)
        tmp_sudoers.write_text(
            f"{username} ALL=(ALL) NOPASSWD: ALL\n",
            encoding="utf-8",
        )
        tmp_sudoers.chmod(0o440)

        try:
            self.ui.log_command("yay -S --noconfirm visual-studio-code-bin")
            chroot_run(
                f"su - {username} -c 'yay -S --noconfirm visual-studio-code-bin'"
            )
            self.ui.log_success("VS Code установлен")
        finally:
            # Удаляем временную запись sudoers
            if tmp_sudoers.exists():
                tmp_sudoers.unlink()

    def _install_claude_code(self, username: str) -> None:
        """Настройка npm-префикса и установка Claude Code.

        Создаёт пользовательский npm-префикс (~/.npm-global),
        добавляет его в PATH через .bashrc и устанавливает
        пакет @anthropic-ai/claude-code.

        Args:
            username: Имя пользователя.
        """
        home_dir = f"/home/{username}"
        npm_prefix = f"{home_dir}/.npm-global"

        # Настройка npm-префикса для пользователя
        self.ui.log_command(f"Настройка npm prefix: {npm_prefix}")
        chroot_run(
            f"su - {username} -c 'mkdir -p {npm_prefix} && npm config set prefix {npm_prefix}'"
        )
        self.ui.log_success("npm prefix настроен")

        # Добавление npm-префикса в PATH через .bashrc
        bashrc_path = f"{home_dir}/.bashrc"
        bashrc_full = MOUNT_POINT / bashrc_path.lstrip("/")

        path_export = (
            f'\n# npm global packages\n'
            f'export PATH="{npm_prefix}/bin:$PATH"\n'
        )

        # Дописываем в существующий .bashrc
        self.ui.log_command(f"Добавление npm prefix в PATH ({bashrc_path})")
        if bashrc_full.exists():
            existing = bashrc_full.read_text(encoding="utf-8")
            bashrc_full.write_text(existing + path_export, encoding="utf-8")
        else:
            bashrc_full.write_text(path_export, encoding="utf-8")

        # Устанавливаем владельца файлов
        chroot_run(["chown", "-R", f"{username}:{username}", home_dir])

        # Установка Claude Code через npm
        self.ui.log_command("npm install -g @anthropic-ai/claude-code")
        chroot_run(
            f"su - {username} -c 'npm install -g @anthropic-ai/claude-code'"
        )
        self.ui.log_success("Claude Code установлен")

    def _run_demo(self) -> None:
        """Демонстрационный режим: имитация установки VS Code и Claude Code."""
        username = self.config.username or "user"

        self.ui.log_command("yay -S --noconfirm visual-studio-code-bin")
        time.sleep(2.0)
        self.ui.log_success("VS Code установлен")

        self.ui.log_command(f"Настройка npm prefix: /home/{username}/.npm-global")
        time.sleep(0.3)
        self.ui.log_success("npm prefix настроен")

        self.ui.log_command(f"Добавление npm prefix в PATH (.bashrc)")
        time.sleep(0.2)
        self.ui.log_success("PATH обновлён")

        self.ui.log_command("npm install -g @anthropic-ai/claude-code")
        time.sleep(1.5)
        self.ui.log_success("Claude Code установлен")

        self.ui.log_success("VS Code и Claude Code установлены")
