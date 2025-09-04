"""
Results handling and data export
Exports results to JSON and CSV
"""
import json
import csv
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, List
try:
    import pandas as pd
    HAS_PANDAS = True
except ImportError:
    HAS_PANDAS = False


logger = logging.getLogger(__name__)


class ResultsManager:
    """Manages export and persistence of scan results"""
    
    def __init__(self, json_file: str, csv_file: str):
        """
        Initialize results manager
        
        Args:
            json_file: Output JSON filename
            csv_file: Output CSV filename
        """
        self.json_file = json_file
        self.csv_file = csv_file
    
    def save_results(self, results: List[Dict]) -> tuple[bool, bool]:
        """
        Save results to JSON and CSV files
        
        Args:
            results: List of dictionaries with scan results
            
        Returns:
            Tuple (json_success, csv_success) indicating success of each export
        """
        json_success = self._save_json(results)
        csv_success = self._save_csv(results)
        
        logger.info(f"Results saved - JSON: {json_success}, CSV: {csv_success}")
        return json_success, csv_success
    
    def _save_json(self, results: List[Dict]) -> bool:
        """
        Save results to JSON file
        
        Args:
            results: List of results
            
        Returns:
            True if successful
        """
        try:
            # Create enhanced data structure with metadata
            output_data = {
                "scan_metadata": {
                    "timestamp": datetime.now().isoformat(),
                    "total_devices": len(results),
                    "scanner_version": "1.0",
                    "scan_type": "BLE_Battery_Analysis"
                },
                "results": results
            }
            
            # Add summary if results exist
            if results:
                summary = self.generate_summary_report(results)
                output_data["summary"] = summary
            
            with open(self.json_file, 'w', encoding='utf-8') as f:
                json.dump(output_data, f, indent=2, ensure_ascii=False)
            
            logger.info(f"JSON results saved to {self.json_file}")
            return True
            
        except Exception as e:
            logger.error(f"error saving JSON: {e}")
            return False
    
    def _save_csv(self, results: List[Dict]) -> bool:
        """
        Save results to CSV file
        
        Args:
            results: List of results
            
        Returns:
            True if successful
        """
        try:
            if not results:
                logger.warning("No results to save to CSV")
                return False
            
            # Define preferred column order (CR2032 enhanced)
            preferred_columns = [
                'macid', 'battery_voltage', 'battery_category', 'status', 'rssi', 
                'timestamp', 'advice', 'percentage_estimate', 'expected_life', 'battery_type'
            ]
            
            # Get all available columns from results
            all_columns = set()
            for result in results:
                all_columns.update(result.keys())
            
            # Order columns: preferred first, then others alphabetically
            ordered_columns = [col for col in preferred_columns if col in all_columns]
            remaining_columns = sorted([col for col in all_columns if col not in preferred_columns])
            final_columns = ordered_columns + remaining_columns
            
            if HAS_PANDAS:
                # Use pandas for better CSV handling
                df = pd.DataFrame(results)
                # Reorder columns
                df = df.reindex(columns=final_columns)
                df.to_csv(self.csv_file, index=False, encoding='utf-8')
            else:
                # Fallback to standard csv module
                with open(self.csv_file, 'w', newline='', encoding='utf-8') as f:
                    writer = csv.DictWriter(f, fieldnames=final_columns)
                    writer.writeheader()
                    writer.writerows(results)
            
            logger.info(f"CSV results saved to {self.csv_file}")
            return True
            
        except Exception as e:
            logger.error(f"error saving CSV: {e}")
            return False
    
    def load_previous_results(self) -> List[Dict]:
        """
        Load previous results from JSON file
        
        Returns:
            List of previous results or empty list if none found
        """
        try:
            with open(self.json_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                
            # Handle both old and new JSON formats
            if isinstance(data, list):
                return data  # Old format
            elif isinstance(data, dict) and 'results' in data:
                return data['results']  # New format
            else:
                return []
                
        except FileNotFoundError:
            logger.info(f"No previous results file found: {self.json_file}")
            return []
        except Exception as e:
            logger.error(f"error loading previous results: {e}")
            return []
    
    def append_results(self, new_results: List[Dict]) -> tuple[bool, bool]:
        """
        Append new results to existing files
        
        Args:
            new_results: New results to append
            
        Returns:
            Tuple (json_success, csv_success)
        """
        try:
            # Load existing results
            existing_results = self.load_previous_results()
            
            # Merge results
            all_results = existing_results + new_results
            
            # Save merged results
            return self.save_results(all_results)
            
        except Exception as e:
            logger.error(f"error appending results: {e}")
            return False, False
    
    def generate_summary_report(self, results: List[Dict]) -> Dict:
        """
        Generate summary report of results
        
        Args:
            results: List of results
            
        Returns:
            Dictionary with scan statistics
        """
        try:
            if not results:
                return {"error": "No results to summarize"}
            
            # Calculate statistics
            total_devices = len(results)
            pass_count = sum(1 for r in results if r.get("status") == "PASS")
            fail_count = total_devices - pass_count
            
            voltages = [r.get("battery_voltage", 0) for r in results if r.get("battery_voltage")]
            avg_voltage = sum(voltages) / len(voltages) if voltages else 0
            min_voltage = min(voltages) if voltages else 0
            max_voltage = max(voltages) if voltages else 0
            
            # Calculate battery percentages
            from .parser import voltage_to_battery_percentage
            percentages = [voltage_to_battery_percentage(v) for v in voltages]
            avg_percentage = sum(percentages) / len(percentages) if percentages else 0
            min_percentage = min(percentages) if percentages else 0
            max_percentage = max(percentages) if percentages else 0
            
            rssi_values = [r.get("rssi", 0) for r in results if r.get("rssi")]
            avg_rssi = sum(rssi_values) / len(rssi_values) if rssi_values else 0
            
            summary = {
                "total_devices": total_devices,
                "pass_count": pass_count,
                "fail_count": fail_count,
                "pass_rate": (pass_count / total_devices * 100) if total_devices > 0 else 0,
                "voltage_stats": {
                    "average": round(avg_voltage, 2),
                    "minimum": min_voltage,
                    "maximum": max_voltage
                },
                "battery_stats": {
                    "average_percentage": round(avg_percentage, 1),
                    "minimum_percentage": round(min_percentage, 1),
                    "maximum_percentage": round(max_percentage, 1)
                },
                "signal_stats": {
                    "average_rssi": round(avg_rssi, 2)
                },
                "scan_timestamp": datetime.now().isoformat()
            }
            
            return summary
            
        except Exception as e:
            logger.error(f"error generating report: {e}")
            return {"error": f"error generating report: {e}"}
    
    def print_summary(self, results: List[Dict]) -> None:
        """
        Print results summary to withsole
        
        Args:
            results: List of results
        """
        try:
            from .parser import format_voltage_with_percentage
            
            summary = self.generate_summary_report(results)
            
            print("\n" + "="*50)
            print("BLE SCAN SUMMARY")
            print("="*50)
            print(f"total devices: {summary.get('total_devices', 0)}")
            print(f"PASS: {summary.get('pass_count', 0)}")
            print(f"FAIL: {summary.get('fail_count', 0)}")
            print(f"Success rate: {summary.get('pass_rate', 0):.1f}%")
            
            voltage_stats = summary.get('voltage_stats', {})
            battery_stats = summary.get('battery_stats', {})
            
            print(f"\nvoltage statistics:")
            print(f"  Average: {voltage_stats.get('average', 0)} mV ({battery_stats.get('average_percentage', 0)}%)")
            print(f"  Minimum: {voltage_stats.get('minimum', 0)} mV ({battery_stats.get('minimum_percentage', 0)}%)")
            print(f"  Maximum: {voltage_stats.get('maximum', 0)} mV ({battery_stats.get('maximum_percentage', 0)}%)")
            
            print(f"\nBatterand statistics:")
            print(f"  Average: {battery_stats.get('average_percentage', 0)}%")
            print(f"  Range: {battery_stats.get('minimum_percentage', 0)}% - {battery_stats.get('maximum_percentage', 0)}%")
            
            signal_stats = summary.get('signal_stats', {})
            print(f"\nAverage signal (RSSI): {signal_stats.get('average_rssi', 0)} dBm")
            
            # Show CR2032 statistics if available
            if results and "battery_category" in results[0]:
                print(f"\nCR2032 battery statistics:")
                categories = {}
                cr2032_percentages = []
                
                for result in results:
                    category = result.get('battery_category', 'UNKNOWN')
                    categories[category] = categories.get(category, 0) + 1
                    if 'percentage_estimate' in result:
                        cr2032_percentages.append(result['percentage_estimate'])
                
                # Show distribution by categories
                for category, count in categories.items():
                    print(f"  {category}: {count} devices")
                
                # CR2032 percentage statistics
                if cr2032_percentages:
                    avg_cr2032 = sum(cr2032_percentages) / len(cr2032_percentages)
                    min_cr2032 = min(cr2032_percentages)
                    max_cr2032 = max(cr2032_percentages)
                    print(f"  Average CR2032 charge: {avg_cr2032:.1f}%")
                    print(f"  Charge range: {min_cr2032:.1f}% - {max_cr2032:.1f}%")
            
            print("\nDevice details:")
            print("-" * 50)
            for result in results:
                mac = result.get('macid', 'UNKNOWN')
                voltage = result.get('battery_voltage', 0)
                status = result.get('status', 'UNKNOWN')
                rssi = result.get('rssi', 0)
                
                # Use CR2032 information if available
                if 'battery_category' in result and 'percentage_estimate' in result:
                    category = result.get('battery_category', 'UNKNOWN')
                    percentage = result.get('percentage_estimate', 0)
                    print(f"{mac}: {voltage}mV ({percentage:.1f}%), {category}, {status}, {rssi}dBm")
                else:
                    # Format voltage with percentage (previous method)
                    voltage_formatted = format_voltage_with_percentage(voltage)
                    print(f"{mac}: {voltage_formatted}, {status}, {rssi}dBm")
            
            print("="*50)
            
        except Exception as e:
            logger.error(f"error printing summarand: {e}")
            
            print("="*50)
            
        except Exception as e:
            logger.error(f"error printing summarand: {e}")


def save_results(results: List[Dict], json_file: str = "battery_scan_results.json", 
                csv_file: str = "battery_scan_results.csv") -> tuple[bool, bool]:
    """
    Convenience function to save results
    
    Args:
        results: List of results
        json_file: Output JSON file
        csv_file: Output CSV file
        
    Returns:
        Tuple (json_success, csv_success)
    """
    manager = ResultsManager(json_file, csv_file)
    return manager.save_results(results)
import json
import csv
logger = logging.getLogger(__name__)


class ResultsManager:
    """Maneja la exportación y persistencia de results de scan"""
    
    def __init__(self, json_file: str, csv_file: str):
        """
        Inicializa el manager de results
        
        Args:
            json_file: Nombre del file JSON de salida
            csv_file: Nombre del file CSV de salida
        """
        self.json_file = json_file
        self.csv_file = csv_file
    
    def save_results(self, results: List[Dict]) -> tuple[bool, bool]:
        """
        Guarda los results en files JSON y CSV
        
        Args:
            results: list de diccionarios with los results del scan
            
        Returns:
            Tupla (json_success, csv_success) indicando el éxito de cada exportación
        """
        json_success = self._save_json(results)
        csv_success = self._save_csv(results)
        
        return json_success, csv_success
    
    def _save_json(self, results: List[Dict]) -> bool:
        """
        Guarda results en formato JSON
        
        Args:
            results: list de results
            
        Returns:
            True si se guardó exitosamente, False en case withtrario
        """
        try:
            # add metadata
            output_data = {
                "scan_metadata": {
                    "total_devices": len(results),
                    "scan_date": datetime.now().isoformat(),
                    "pass_count": sum(1 for r in results if r.get("status") == "PASS"),
                    "fail_count": sum(1 for r in results if r.get("status") == "FAIL")
                },
                "results": results
            }
            
            with open(self.json_file, 'w', encoding='utf-8') as f:
                json.dump(output_data, f, indent=2, ensure_ascii=False)
            
            logger.info(f"results guardados en JSON: {self.json_file}")
            return True
            
        except Exception as e:
            logger.error(f"error saving JSON: {e}")
            return False
    
    def _save_csv(self, results: List[Dict]) -> bool:
        """
        Guarda results en formato CSV
        
        Args:
            results: list de results
            
        Returns:
            True si se guardó exitosamente, False en case withtrario
        """
        try:
            if not results:
                logger.warning("No hay results for save en CSV")
                return False
            
            # use pandas for mejor manejo del CSV
            df = pd.DataFrame(results)
            
            # Reordenar columnas for mejor presentación
            columns_order = ["macid", "rssi", "battery_voltage", "battery_category", "status", "timestamp"]
            
            # add columnas CR2032 si están presentes
            if results and "advice" in results[0]:
                columns_order.extend(["advice", "percentage_estimate", "expected_life", "battery_type"])
            
            # Reordenar solo las columnas que existen
            existing_columns = [col for col in columns_order if col in df.columns]
            df = df.reindex(columns=existing_columns)
            
            # save CSV
            df.to_csv(self.csv_file, index=False, encoding='utf-8')
            
            logger.info(f"results guardados en CSV: {self.csv_file}")
            return True
            
        except Exception as e:
            logger.error(f"error saving CSV: {e}")
            return False
    
    def load_previous_results(self) -> List[Dict]:
        """
        Carga results previos from el file JSON
        
        Returns:
            list de results previos o list vacía si no existen
        """
        try:
            if not Path(self.json_file).exists():
                return []
            
            with open(self.json_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # Extraer solo los results
            if isinstance(data, dict) and "results" in data:
                return data["results"]
            elif isinstance(data, list):
                return data
            else:
                logger.warning("File format JSON no rewithocido")
                return []
                
        except Exception as e:
            logger.error(f"error loading results previos: {e}")
            return []
    
    def append_results(self, new_results: List[Dict]) -> tuple[bool, bool]:
        """
        Agrega nuevos results a los existentes
        
        Args:
            new_results: Nuevos results a add
            
        Returns:
            Tupla (json_success, csv_success)
        """
        try:
            # load results existentes
            existing_results = self.load_previous_results()
            
            # Combinar results
            all_results = existing_results + new_results
            
            # Save results combinados
            return self.save_results(all_results)
            
        except Exception as e:
            logger.error(f"error agregando results: {e}")
            return False, False
    
    def generate_summary_report(self, results: List[Dict]) -> Dict:
        """
        Genera un report summary de los results
        
        Args:
            results: list de results
            
        Returns:
            Diccionario with statistics del scan
        """
        try:
            if not results:
                return {"error": "No hay results for analyze"}
            
            # import function de withversión de porcentaje
            from .parser import voltage_to_battery_percentage
            
            # calculate statistics
            total_devices = len(results)
            pass_count = sum(1 for r in results if r.get("status") == "PASS")
            fail_count = sum(1 for r in results if r.get("status") == "FAIL")
            
            voltages = [r.get("battery_voltage", 0) for r in results if r.get("battery_voltage")]
            avg_voltage = sum(voltages) / len(voltages) if voltages else 0
            min_voltage = min(voltages) if voltages else 0
            max_voltage = max(voltages) if voltages else 0
            
            # calculate porcentajes de battery
            percentages = [voltage_to_battery_percentage(v) for v in voltages]
            avg_percentage = sum(percentages) / len(percentages) if percentages else 0
            min_percentage = min(percentages) if percentages else 0
            max_percentage = max(percentages) if percentages else 0
            
            rssi_values = [r.get("rssi", 0) for r in results if r.get("rssi")]
            avg_rssi = sum(rssi_values) / len(rssi_values) if rssi_values else 0
            
            summary = {
                "total_devices": total_devices,
                "pass_count": pass_count,
                "fail_count": fail_count,
                "pass_rate": (pass_count / total_devices * 100) if total_devices > 0 else 0,
                "voltage_stats": {
                    "average": round(avg_voltage, 2),
                    "minimum": min_voltage,
                    "maximum": max_voltage
                },
                "battery_stats": {
                    "average_percentage": round(avg_percentage, 1),
                    "minimum_percentage": round(min_percentage, 1),
                    "maximum_percentage": round(max_percentage, 1)
                },
                "signal_stats": {
                    "average_rssi": round(avg_rssi, 2)
                },
                "scan_timestamp": datetime.now().isoformat()
            }
            
            return summary
            
        except Exception as e:
            logger.error(f"error generando report: {e}")
            return {"error": f"error generando report: {e}"}
    
    def print_summary(self, results: List[Dict]) -> None:
        """
        Imprime un summary de los results en la withsola
        
        Args:
            results: list de results
        """
        try:
            from .parser import format_voltage_with_percentage
            
            summary = self.generate_summary_report(results)
            
            print("\n" + "="*50)
            print("BLE SCAN SUMMARY")
            print("="*50)
            print(f"Total devices: {summary.get('total_devices', 0)}")
            print(f"PASS: {summary.get('pass_count', 0)}")
            print(f"FAIL: {summary.get('fail_count', 0)}")
            print(f"Success rate: {summary.get('pass_rate', 0):.1f}%")
            
            voltage_stats = summary.get('voltage_stats', {})
            battery_stats = summary.get('battery_stats', {})
            
            print(f"\nEstadísticas de voltage:")
            print(f"  average: {voltage_stats.get('average', 0)} mV ({battery_stats.get('average_percentage', 0)}%)")
            print(f"  minimum: {voltage_stats.get('minimum', 0)} mV ({battery_stats.get('minimum_percentage', 0)}%)")
            print(f"  maximum: {voltage_stats.get('maximum', 0)} mV ({battery_stats.get('maximum_percentage', 0)}%)")
            
            print(f"\nEstadísticas de battery:")
            print(f"  average: {battery_stats.get('average_percentage', 0)}%")
            print(f"  Rango: {battery_stats.get('minimum_percentage', 0)}% - {battery_stats.get('maximum_percentage', 0)}%")
            
            signal_stats = summary.get('signal_stats', {})
            print(f"\nAverage signal (RSSI): {signal_stats.get('average_rssi', 0)} dBm")
            
            # show statistics CR2032 si están disponibles
            if results and "battery_category" in results[0]:
                print(f"\nEstadísticas de CR2032 batteries:")
                categories = {}
                cr2032_percentages = []
                
                for result in results:
                    category = result.get('battery_category', 'UNKNOWN')
                    categories[category] = categories.get(category, 0) + 1
                    if 'percentage_estimate' in result:
                        cr2032_percentages.append(result['percentage_estimate'])
                
                # show distribución por categories
                for category, count in categories.items():
                    print(f"  {category}: {count} devices")
                
                # statistics de porcentaje CR2032
                if cr2032_percentages:
                    avg_cr2032 = sum(cr2032_percentages) / len(cr2032_percentages)
                    min_cr2032 = min(cr2032_percentages)
                    max_cr2032 = max(cr2032_percentages)
                    print(f"  Carga average CR2032: {avg_cr2032:.1f}%")
                    print(f"  Charge range: {min_cr2032:.1f}% - {max_cr2032:.1f}%")
            
            print("\nDetalles por device:")
            print("-" * 50)
            for result in results:
                mac = result.get('macid', 'UNKNOWN')
                voltage = result.get('battery_voltage', 0)
                status = result.get('status', 'UNKNOWN')
                rssi = result.get('rssi', 0)
                
                # use information CR2032 si está available
                if 'battery_category' in result and 'percentage_estimate' in result:
                    category = result.get('battery_category', 'UNKNOWN')
                    percentage = result.get('percentage_estimate', 0)
                    print(f"{mac}: {voltage}mV ({percentage:.1f}%), {category}, {status}, {rssi}dBm")
                else:
                    # Format voltage with percentage (legacy method)
                    voltage_formatted = format_voltage_with_percentage(voltage)
                    print(f"{mac}: {voltage_formatted}, {status}, {rssi}dBm")
            
            print("="*50)
            
        except Exception as e:
            logger.error(f"error imprimiendo summarand: {e}")


def save_results(results: List[Dict], json_file: str = "battery_scan_results.json", 
                csv_file: str = "battery_scan_results.csv") -> tuple[bool, bool]:
    """
    function de withveniencia for save results
    
    Args:
        results: list de results
        json_file: file JSON de salida
        csv_file: file CSV de salida
        
    Returns:
        Tupla (json_success, csv_success)
    """
    manager = ResultsManager(json_file, csv_file)
    return manager.save_results(results)
