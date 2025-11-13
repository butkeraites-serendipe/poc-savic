import os
import requests
from pathlib import Path
from typing import Optional, Dict, Any, Tuple
from dotenv import load_dotenv

# Carrega as variáveis de ambiente
env_path = Path(__file__).parent / ".env"
load_dotenv(dotenv_path=env_path)
load_dotenv()


def get_api_key() -> Optional[str]:
    """Retorna a chave da API Google Maps do arquivo .env."""
    api_key = os.getenv("GOOGLE_MAPS_API_KEY")
    if api_key:
        api_key = api_key.strip()
    return api_key


def formatar_endereco_para_geocode(address: Dict[str, Any]) -> str:
    """
    Formata o endereço do CNPJA para string de geocoding.
    
    Args:
        address: Dicionário com dados do endereço da API CNPJA
    
    Returns:
        String formatada para geocoding
    """
    partes = []
    
    if address.get("street"):
        partes.append(address["street"])
    if address.get("number"):
        partes.append(str(address["number"]))
    if address.get("district"):
        partes.append(address["district"])
    if address.get("city"):
        partes.append(address["city"])
    if address.get("state"):
        partes.append(address["state"])
    
    return ", ".join(partes)


def geocode_endereco(endereco: str) -> Optional[Dict[str, Any]]:
    """
    Converte endereço em coordenadas (lat, lng) usando Google Geocoding API.
    
    Args:
        endereco: Endereço formatado como string
    
    Returns:
        Dicionário com lat, lng e informações adicionais, ou None se erro
    """
    api_key = get_api_key()
    
    if not api_key:
        raise ValueError("Chave da API Google Maps não configurada. Verifique GOOGLE_MAPS_API_KEY no arquivo .env")
    
    url = "https://maps.googleapis.com/maps/api/geocode/json"
    params = {
        "address": endereco,
        "key": api_key
    }
    
    try:
        response = requests.get(url, params=params, timeout=10)
        data = response.json()
        
        if data.get("status") == "OK" and data.get("results"):
            result = data["results"][0]
            location = result["geometry"]["location"]
            
            return {
                "lat": location["lat"],
                "lng": location["lng"],
                "formatted_address": result.get("formatted_address", ""),
                "place_id": result.get("place_id", ""),
                "types": result.get("types", []),
                "full_result": result
            }
        elif data.get("status") == "ZERO_RESULTS":
            return None
        else:
            raise ValueError(f"Erro no geocoding: {data.get('status', 'UNKNOWN_ERROR')}")
            
    except requests.exceptions.RequestException as e:
        raise ValueError(f"Erro ao fazer geocoding: {str(e)}")


def verificar_street_view(lat: float, lng: float) -> Dict[str, Any]:
    """
    Verifica se existe Street View disponível para as coordenadas.
    
    Args:
        lat: Latitude
        lng: Longitude
    
    Returns:
        Dicionário com status e informações do Street View
    """
    api_key = get_api_key()
    
    if not api_key:
        raise ValueError("Chave da API Google Maps não configurada.")
    
    url = "https://maps.googleapis.com/maps/api/streetview/metadata"
    params = {
        "location": f"{lat},{lng}",
        "key": api_key
    }
    
    try:
        response = requests.get(url, params=params, timeout=10)
        data = response.json()
        
        return {
            "status": data.get("status", "UNKNOWN"),
            "copyright": data.get("copyright", ""),
            "date": data.get("date", ""),
            "location": data.get("location", {}),
            "pano_id": data.get("pano_id", "")
        }
        
    except requests.exceptions.RequestException as e:
        raise ValueError(f"Erro ao verificar Street View: {str(e)}")


def obter_imagem_street_view(lat: float, lng: float, heading: int = 90, pitch: int = 0, fov: int = 90, size: str = "1280x720") -> Optional[bytes]:
    """
    Obtém imagem do Street View para as coordenadas.
    
    Args:
        lat: Latitude
        lng: Longitude
        heading: Direção da câmera (0-360, 0=norte)
        pitch: Ângulo vertical da câmera (-90 a 90)
        fov: Campo de visão (10 a 120)
        size: Tamanho da imagem (ex: "1280x720")
    
    Returns:
        Bytes da imagem ou None se erro
    """
    api_key = get_api_key()
    
    if not api_key:
        raise ValueError("Chave da API Google Maps não configurada.")
    
    url = "https://maps.googleapis.com/maps/api/streetview"
    params = {
        "size": size,
        "location": f"{lat},{lng}",
        "heading": str(heading),
        "pitch": str(pitch),
        "fov": str(fov),
        "key": api_key
    }
    
    try:
        response = requests.get(url, params=params, timeout=10)
        
        if response.status_code == 200 and response.headers.get("content-type", "").startswith("image"):
            return response.content
        else:
            return None
            
    except requests.exceptions.RequestException as e:
        raise ValueError(f"Erro ao obter imagem Street View: {str(e)}")


def buscar_place_id_por_endereco(endereco: str) -> Optional[str]:
    """
    Busca place_id usando Places API Text Search.
    
    Args:
        endereco: Endereço formatado
    
    Returns:
        place_id ou None
    """
    api_key = get_api_key()
    
    if not api_key:
        raise ValueError("Chave da API Google Maps não configurada.")
    
    url = "https://maps.googleapis.com/maps/api/place/textsearch/json"
    params = {
        "query": endereco,
        "key": api_key
    }
    
    try:
        response = requests.get(url, params=params, timeout=10)
        data = response.json()
        
        if data.get("status") == "OK" and data.get("results"):
            return data["results"][0].get("place_id")
        
        return None
        
    except requests.exceptions.RequestException as e:
        return None


def obter_fotos_place(place_id: str, max_photos: int = 3) -> list:
    """
    Obtém fotos de um lugar usando Places API.
    
    Args:
        place_id: ID do lugar no Google Places
        max_photos: Número máximo de fotos a retornar
    
    Returns:
        Lista de dicionários com informações das fotos
    """
    api_key = get_api_key()
    
    if not api_key:
        raise ValueError("Chave da API Google Maps não configurada.")
    
    url = "https://maps.googleapis.com/maps/api/place/details/json"
    params = {
        "place_id": place_id,
        "fields": "photos",
        "key": api_key
    }
    
    try:
        response = requests.get(url, params=params, timeout=10)
        data = response.json()
        
        if data.get("status") == "OK" and data.get("result", {}).get("photos"):
            photos = data["result"]["photos"][:max_photos]
            return [
                {
                    "photo_reference": photo.get("photo_reference", ""),
                    "width": photo.get("width", 0),
                    "height": photo.get("height", 0)
                }
                for photo in photos
            ]
        
        return []
        
    except requests.exceptions.RequestException as e:
        return []


def obter_imagem_place(photo_reference: str, maxwidth: int = 800) -> Optional[bytes]:
    """
    Obtém imagem de um lugar usando photo_reference.
    
    Args:
        photo_reference: Referência da foto
        maxwidth: Largura máxima da imagem
    
    Returns:
        Bytes da imagem ou None
    """
    api_key = get_api_key()
    
    if not api_key:
        raise ValueError("Chave da API Google Maps não configurada.")
    
    url = "https://maps.googleapis.com/maps/api/place/photo"
    params = {
        "maxwidth": str(maxwidth),
        "photoreference": photo_reference,
        "key": api_key
    }
    
    try:
        response = requests.get(url, params=params, timeout=10)
        
        if response.status_code == 200 and response.headers.get("content-type", "").startswith("image"):
            return response.content
        else:
            return None
            
    except requests.exceptions.RequestException as e:
        return None


def processar_endereco_completo(address: Dict[str, Any]) -> Dict[str, Any]:
    """
    Processa endereço completo: geocoding, Street View e Places.
    
    Args:
        address: Dicionário com dados do endereço da API CNPJA
    
    Returns:
        Dicionário com todas as informações coletadas
    """
    resultado = {
        "geocoding": None,
        "street_view": None,
        "street_view_image": None,
        "place_photos": [],
        "erros": []
    }
    
    try:
        # 1. Formatar e fazer geocoding
        endereco_formatado = formatar_endereco_para_geocode(address)
        geocoding = geocode_endereco(endereco_formatado)
        
        if not geocoding:
            resultado["erros"].append("Endereço não encontrado no geocoding")
            return resultado
        
        resultado["geocoding"] = geocoding
        lat = geocoding["lat"]
        lng = geocoding["lng"]
        
        # 2. Verificar Street View
        try:
            street_view_meta = verificar_street_view(lat, lng)
            resultado["street_view"] = street_view_meta
            
            # 3. Obter imagem Street View se disponível
            if street_view_meta.get("status") == "OK":
                # Tenta diferentes headings para encontrar melhor ângulo da fachada
                for heading in [0, 90, 180, 270]:
                    imagem = obter_imagem_street_view(lat, lng, heading=heading, pitch=0, fov=90)
                    if imagem:
                        resultado["street_view_image"] = {
                            "image_bytes": imagem,
                            "heading": heading,
                            "lat": lat,
                            "lng": lng
                        }
                        break
        except Exception as e:
            resultado["erros"].append(f"Erro ao processar Street View: {str(e)}")
        
        # 4. Tentar obter fotos do Places
        try:
            place_id = geocoding.get("place_id")
            if not place_id:
                # Tenta buscar por endereço
                place_id = buscar_place_id_por_endereco(endereco_formatado)
            
            if place_id:
                fotos = obter_fotos_place(place_id, max_photos=3)
                for foto in fotos:
                    photo_ref = foto.get("photo_reference")
                    if photo_ref:
                        imagem = obter_imagem_place(photo_ref, maxwidth=800)
                        if imagem:
                            resultado["place_photos"].append({
                                "image_bytes": imagem,
                                "photo_reference": photo_ref,
                                "width": foto.get("width", 0),
                                "height": foto.get("height", 0)
                            })
        except Exception as e:
            resultado["erros"].append(f"Erro ao processar Places: {str(e)}")
        
    except Exception as e:
        resultado["erros"].append(f"Erro geral: {str(e)}")
    
    return resultado

