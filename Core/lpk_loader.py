from __future__ import unicode_literals
from typing import Tuple
import zipfile
import json
from Core.utils import *
import logging
import os

logger = logging.getLogger("lpkLoder")

class LpkLoader():
    def __init__(self, lpkpath, configpath=None) -> None:
        self.lpkpath = lpkpath
        self.configpath = configpath
        self.trans = {}
        self.entrys = {}
        self.config = None
        self.load_lpk()
    
    def load_lpk(self):
        self.lpkfile = zipfile.ZipFile(self.lpkpath)

        config_mlve_raw = self.lpkfile.read(hashed_filename("config.mlve")).decode()
        self.mlve_config = json.loads(config_mlve_raw)

        logger.debug(f"mlve config:\n {self.mlve_config}")
        if self.mlve_config["type"] == "STM_1_0":
            if not self.configpath:
                raise ValueError("Steam Workshop LPK文件需要config.json文件进行解密，请使用 -c 参数指定配置文件路径")
            self.load_config()
    
    def load_config(self):
        self.config = json.loads(open(self.configpath, "r", encoding="utf8").read())

    def get_character_name(self, chara, char_idx):
        # 首先尝试从config.json获取title
        if hasattr(self, 'config') and self.config and 'title' in self.config:
            title = self.config['title']
            if title and title.strip():
                sanitized_title = sanitize_folder_name(title)
                print(f"  使用config.json中的title: {title} -> {sanitized_title}")
                return sanitized_title
        
        # 其次使用chara中的character字段
        if chara["character"] and chara["character"].strip():
            character_name = sanitize_folder_name(chara["character"])
            return character_name
        
        # 最后使用默认名称
        return f"character_{char_idx}"

    def extract(self, outputdir: str):
        total_characters = len(self.mlve_config["list"])
        print(f"发现 {total_characters} 个角色模型")
        
        for char_idx, chara in enumerate(self.mlve_config["list"], 1):
            chara_name = self.get_character_name(chara, char_idx)
            subdir = os.path.join(outputdir, chara_name)
            os.makedirs(subdir, exist_ok=True)
            
            print(f"\n[{char_idx}/{total_characters}] 正在解包角色: {chara_name}")
            
            total_costumes = len(chara["costume"])
            if total_costumes > 1:
                print(f"  发现 {total_costumes} 套服装")

            for i in range(total_costumes):
                if total_costumes > 1:
                    print(f"  [{i+1}/{total_costumes}] 解包服装 {i+1}")
                else:
                    print(f"  正在解包模型文件...")
                    
                try:
                    self.extract_costume(chara["costume"][i], subdir)
                except Exception as e:
                    print(f"  警告: 服装 {i+1} 解包失败: {e}")
                    continue

            print(f"  正在生成模型配置文件...")
            for name in self.entrys:
                out_s: str = self.entrys[name]
                for k in self.trans:
                    out_s = out_s.replace(k, self.trans[k])
                
                model_content = out_s.encode('utf-8')
                self.save_file_with_structure(name, model_content, subdir)
            
            print(f"  ✓ 角色 {chara_name} 解包完成")
    
    def extract_costume(self, costume: dict, dir: str):
        if costume["path"] == "":
            return

        filename :str = costume["path"]

        self.check_decrypt(filename)

        self.extract_model_json(filename, dir)

    def extract_model_json(self, model_json: str, dir):
        logger.debug(f"========= extracting model {model_json} =========")
        if model_json in self.trans:
            return

        subdir = dir
        entry_s = self.decrypt_file(model_json).decode(encoding="utf8")
        entry = json.loads(entry_s)

        out_s = json.dumps(entry, ensure_ascii=False)
        id = len(self.entrys)

        self.entrys[f"model{id}.model3.json"] = out_s

        self.trans[model_json] = f"model{id}.model3.json"

        logger.debug(f"model{id}.model3.json:\n{entry}")

        for name, val in travels_dict(entry):
            logger.debug(f"{name} -> {val}")
            if (name.lower().endswith("_command") or name.lower().endswith("_postcommand")) and val:
                commands = val.split(";")
                for cmd in commands:
                    enc_file = find_encrypted_file(cmd)
                    if enc_file == None:
                        continue

                    if cmd.startswith("change_cos"):
                        enc_file = find_encrypted_file(cmd)
                        self.extract_model_json(enc_file, dir)
                    else:
                        name += f"_{id}"
                        _, suffix = self.recovery(enc_file, os.path.join(subdir, name))
                        saved_path = self.get_relative_path(name + suffix, subdir)
                        self.trans[enc_file] = saved_path


            if is_encrypted_file(val):
                enc_file = val
                if enc_file in self.trans:
                    continue
                else:
                    name += f"_{id}"
                    _, suffix = self.recovery(enc_file, os.path.join(subdir, name))
                    saved_path = self.get_relative_path(name + suffix, subdir)
                    self.trans[enc_file] = saved_path
        
        logger.debug(f"========= end of model {model_json} =========")


    def check_decrypt(self, filename):
        '''
        Check if decryption work.

        If lpk earsed fileId in config.json, this function will automatically try to use lpkFile as fileId.
        If all attemptions failed, this function will read fileId from ``STDIN``.
        '''

        logger.info("try to decrypt entry model.json")

        try:
            self.decrypt_file(filename).decode(encoding="utf8")
        except UnicodeDecodeError:
            logger.info("trying to auto fix fileId")
            success = False
            possible_fileId = []
            possible_fileId.append(self.config["lpkFile"].strip('.lpk'))
            for fileid in possible_fileId:
                self.config["fileId"] = fileid
                try:
                    self.decrypt_file(filename).decode(encoding="utf8")
                except UnicodeDecodeError:
                    continue

                success = True
                break
            if not success:
                print("steam workshop fileid is usually a foler under PATH_TO_YOUR_STEAM/steamapps/workshop/content/616720/([0-9]+)")
                fileid = input("auto fix failed, please input fileid manually: ")
                self.config["fileId"] = fileid
                try:
                    self.decrypt_file(filename).decode(encoding="utf8")
                except UnicodeDecodeError:
                    logger.fatal("decrypt failed!")
                    exit(0)

    def save_file_with_structure(self, filename, content, base_output_path, original_name=""):
        """按标准Live2D结构保存文件"""
        file_ext = os.path.splitext(filename)[1].lower()
        filename_lower = filename.lower()
        original_lower = original_name.lower() if original_name else ""
        
        if file_ext in ['.png', '.jpg', '.jpeg', '.bmp', '.tga']:
            subfolder = 'textures'
        elif 'motion' in filename_lower and file_ext == '.json':
            filename = filename.replace('.json', '.motion3.json')
            if 'idle' in filename_lower or 'idle' in original_lower:
                subfolder = 'motions/idle'
            elif 'tap' in filename_lower or 'touch' in filename_lower or 'tap' in original_lower:
                subfolder = 'motions/tap'
            elif 'flick' in filename_lower or 'flick' in original_lower:
                subfolder = 'motions/flick'
            elif 'pinch' in filename_lower or 'pinch' in original_lower:
                subfolder = 'motions/pinch'
            else:
                subfolder = 'motions'
        elif ('expression' in filename_lower or 'exp' in filename_lower or 
              'expression' in original_lower or 'exp' in original_lower) and file_ext == '.json':
            filename = filename.replace('.json', '.exp3.json')
            subfolder = 'expressions'
        elif 'physics' in filename_lower and file_ext == '.json':
            filename = filename.replace('.json', '.physic3.json')
            subfolder = 'physics'
        elif 'pose' in filename_lower and file_ext == '.json':
            filename = filename.replace('.json', '.pose.json')
            subfolder = 'pose'
        elif 'effect' in filename_lower and file_ext == '.json':
            subfolder = 'effects'
        elif 'userdata' in filename_lower and file_ext == '.json':
            subfolder = 'userdata'
        elif file_ext == '.moc3':
            subfolder = ''  # MOC3文件放根目录
        elif filename_lower.endswith('.model3.json'):
            subfolder = ''  # 主配置文件放根目录
        elif file_ext in ['.wav', '.mp3', '.ogg']:
            subfolder = 'sounds'
        else:
            subfolder = ''  # 其他文件直接放根目录
        
        if subfolder:
            final_path = os.path.join(base_output_path, subfolder, filename)
            os.makedirs(os.path.join(base_output_path, subfolder), exist_ok=True)
        else:
            final_path = os.path.join(base_output_path, filename)
            os.makedirs(base_output_path, exist_ok=True)
        
        with open(final_path, 'wb') as f:
            f.write(content)
        
        return final_path

    def get_relative_path(self, filename, base_dir):
        """获取文件相对于模型根目录的路径"""
        file_ext = os.path.splitext(filename)[1].lower()
        filename_lower = filename.lower()
        
        # 根据文件类型返回相对路径
        if file_ext in ['.png', '.jpg', '.jpeg', '.bmp', '.tga']:
            return f"textures/{filename}"
        elif 'motion' in filename_lower and file_ext == '.json':
            if 'idle' in filename_lower:
                return f"motions/idle/{filename}".replace('.json', '.motion3.json')
            elif 'tap' in filename_lower or 'touch' in filename_lower:
                return f"motions/tap/{filename}".replace('.json', '.motion3.json')
            elif 'flick' in filename_lower:
                return f"motions/flick/{filename}".replace('.json', '.motion3.json')
            elif 'pinch' in filename_lower:
                return f"motions/pinch/{filename}".replace('.json', '.motion3.json')
            else:
                return f"motions/{filename}".replace('.json', '.motion3.json')
        elif ('expression' in filename_lower or 'exp' in filename_lower) and file_ext == '.json':
            return f"expressions/{filename}".replace('.json', '.exp3.json')
        elif 'physics' in filename_lower and file_ext == '.json':
            return f"physics/{filename}".replace('.json', '.physic3.json')
        elif 'pose' in filename_lower and file_ext == '.json':
            return f"pose/{filename}".replace('.json', '.pose.json')
        elif 'effect' in filename_lower and file_ext == '.json':
            return f"effects/{filename}"
        elif 'userdata' in filename_lower and file_ext == '.json':
            return f"userdata/{filename}"
        elif file_ext in ['.wav', '.mp3', '.ogg']:
            return f"sounds/{filename}"
        elif file_ext == '.moc3' or filename_lower.endswith('.model3.json'):
            return filename  # 根目录
        else:
            return filename  # 其他文件也放在根目录

    def recovery(self, filename, output) -> Tuple[bytes, str]:
        ret = self.decrypt_file(filename)
        suffix = guess_type(ret)
        base_dir = os.path.dirname(output)
        base_filename = os.path.basename(output) + suffix
        final_path = self.save_file_with_structure(base_filename, ret, base_dir, filename)
        relative_path = os.path.relpath(final_path, base_dir)
        print(f"    ✓ {filename} -> {relative_path}")
        
        return ret, suffix

    def getkey(self, file: str):
        if self.mlve_config["type"] == "STM_1_0" and self.mlve_config["encrypt"] != "true":
            return 0

        if self.mlve_config["type"] == "STM_1_0":
            return genkey(self.mlve_config["id"] + self.config["fileId"] + file + self.config["metaData"])
        elif self.mlve_config["type"] == "STD2_0":
            return genkey(self.mlve_config["id"] + file)
        else:
            raise Exception(f"not support type {self.mlve_config['type']}")

    def decrypt_file(self, filename) -> bytes:
        data = self.lpkfile.read(filename)
        return self.decrypt_data(filename, data)

    def decrypt_data(self, filename: str, data: bytes) -> bytes:
        key = self.getkey(filename)
        return decrypt(key, data)
